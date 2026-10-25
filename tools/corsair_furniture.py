"""Furniture modelled for the Old Corsair: what the decoration mods lack (or not close enough to the
interior views of the reference sheet). The mods' furniture (tables, benches, chairs, stoves, crates,
barrels lying down, shelves, lanterns, bottles...) is placed by tools/corsair_decor.py; these pieces are
drawn in the ship's model by tools/generate_corsair.py, in the ship's texture regions
(tools/corsair_texture.py).

Every builder takes the bone, a name prefix and its placement (ship-local blocks). Element names start
with "lit" (shaded like the rooms) or "glow" (full bright).
"""
import math

import numpy as np

import generate_galleon as gn
import generate_galley as gg
import nautilus_furniture as nf
import ship_details as sd

v3, norm, add_cube, beam = gg.v3, gg.norm, gg.add_cube, gg.beam
ry = gg.ry
disc, turned, round_bar = gn.disc, gn.turned, gn.round_bar
EYE = np.eye(3)


def captain_bed(bone, name, p, l=2.0, w=1.3):
    """The captain's bed (reference panel 3): a dark carved frame on turned posts, the red blanket over
    the side rails and folded back at the head, a white pillow; the head against the stern windows."""
    p = v3(*p)
    head, foot = -l / 2, l / 2
    add_cube(bone, "lit_" + name + "_frame", p + v3(0, 0.3, 0), EYE, (w, 0.22, l), "wood_dark")
    add_cube(bone, "lit_" + name + "_mattress", p + v3(0, 0.47, 0.02), EYE, (w - 0.12, 0.14, l - 0.16), "linen")
    add_cube(bone, "lit_" + name + "_blanket", p + v3(0, 0.56, 0.18), EYE, (w - 0.04, 0.07, l - 0.5), {"all": "bedding"}, stretch=True)
    for s in (1, -1):
        add_cube(bone, "lit_%s_drape_%d" % (name, s > 0), p + v3(s * (w / 2 - 0.01), 0.45, 0.18), EYE, (0.03, 0.24, l - 0.5),
                 {"all": "bedding"}, stretch=True)
    add_cube(bone, "lit_" + name + "_fold", p + v3(0, 0.6, head + 0.62), EYE, (w - 0.03, 0.05, 0.26), "linen")
    add_cube(bone, "lit_" + name + "_pillow", p + v3(0, 0.62, head + 0.3), EYE, (w - 0.4, 0.13, 0.36), "linen")
    for k, (sx, sz) in enumerate(((1, -1), (-1, -1), (1, 1), (-1, 1))):
        top = 1.25 if sz < 0 else 0.85
        q = p + v3(sx * (w / 2 - 0.06), 0, sz * (l / 2 - 0.06))
        turned(bone, "lit_%s_post_%d" % (name, k), q, q + v3(0, top, 0), [(0, 0.13), (0.3, 0.1), (0.85, 0.12), (1, 0)], "wood_dark")
        disc(bone, "lit_%s_knob_%d" % (name, k), q + v3(0, top + 0.03, 0), (0, 1, 0), 0.07, 0.07, "bronze")
    add_cube(bone, "lit_" + name + "_headboard", p + v3(0, 0.78, head + 0.06), EYE, (w - 0.16, 0.85, 0.07), {"all": "wood_dark", "+3": "carving"},
             stretch=True)
    add_cube(bone, "lit_" + name + "_footboard", p + v3(0, 0.55, foot - 0.06), EYE, (w - 0.16, 0.45, 0.07), "wood_dark")


def chest(bone, name, p, yaw=0.0, w=1.0, d=0.55):
    """Sea chest: planked body, a domed lid, iron bands and corner plates, a bronze lock, rope handles."""
    p = v3(*p)
    R = ry(yaw)
    add_cube(bone, "lit_" + name, p + v3(0, 0.26, 0), R, (w, 0.5, d), "wood_mid")
    add_cube(bone, "lit_" + name + "_lid", p + v3(0, 0.55, 0), R, (w + 0.04, 0.1, d + 0.04), "wood_dark")
    add_cube(bone, "lit_" + name + "_dome", p + v3(0, 0.62, 0), R, (w + 0.02, 0.06, d - 0.18), "wood_dark")
    for k, sx in enumerate((-0.36, 0.0, 0.36)):
        add_cube(bone, "lit_%s_band_%d" % (name, k), p + R @ v3(sx * w, 0.33, 0), R, (0.06, 0.6, d + 0.07), "iron")
    add_cube(bone, "lit_" + name + "_lock", p + R @ v3(0, 0.44, d / 2 + 0.03), R, (0.14, 0.16, 0.03), "bronze")
    for s in (1, -1):
        beam(bone, "lit_%s_handle_%d" % (name, s > 0), p + R @ v3(s * (w / 2 + 0.03), 0.38, -0.12), p + R @ v3(s * (w / 2 + 0.03), 0.38, 0.12),
             0.04, "rope")


def chart_sheet(bone, name, p, yaw=0.3):
    nf.chart_sheet(bone, name, p, yaw)


def compass_box(bone, name, p):
    """A brass compass in its wooden box and a pair of dividers, on the captain's desk."""
    p = v3(*p)
    add_cube(bone, "lit_" + name + "_box", p + v3(0, 0.05, 0), EYE, (0.28, 0.1, 0.28), "wood_dark")
    disc(bone, "lit_" + name + "_dial", p + v3(0, 0.105, 0), (0, 1, 0), 0.11, 0.012, {"all": "bronze", "+2": "compass"})
    beam(bone, "lit_" + name + "_divider_0", p + v3(0.2, 0.01, 0.15), p + v3(0.4, 0.05, -0.05), 0.02, "iron")
    beam(bone, "lit_" + name + "_divider_1", p + v3(0.32, 0.01, 0.2), p + v3(0.4, 0.05, -0.05), 0.02, "iron")


def wall_chart(bone, name, center, normal, w, h):
    """A sea chart in a plain dark frame on a wall whose inner side faces `normal`."""
    R, u, n = nf.frame(normal)
    c = v3(*center) + n * 0.03
    add_cube(bone, "lit_" + name, c, R, (w, h, 0.02), {"all": "wood_dark", "+3": "chart"}, stretch=True, u_dir=u, v_dir=v3(0, -1, 0))
    t = 0.07
    for k, (dx, dy, sw, sh) in enumerate(((0, h / 2 + t / 2, w + 2 * t, t), (0, -h / 2 - t / 2, w + 2 * t, t),
                                          (w / 2 + t / 2, 0, t, h), (-w / 2 - t / 2, 0, t, h))):
        add_cube(bone, "lit_%s_frame%d" % (name, k), c + u * dx + v3(0, dy, 0) + n * 0.015, R, (sw, sh, 0.06), "wood_dark")


def telescope(bone, name, p, facing):
    """A brass telescope on its wooden tripod (navigation instruments of the reference)."""
    nf.telescope(bone, name, p, facing)


def tankards(bone, name, pts):
    """Wooden tankards with iron hoops and a handle, on the common room's table."""
    for k, q in enumerate(pts):
        q = v3(*q)
        disc(bone, "lit_%s_%d" % (name, k), q + v3(0, 0.09, 0), (0, 1, 0), 0.075, 0.18, "wood_mid")
        disc(bone, "lit_%s_%d_hoop" % (name, k), q + v3(0, 0.13, 0), (0, 1, 0), 0.08, 0.025, "iron")
        add_cube(bone, "lit_%s_%d_handle" % (name, k), q + v3(0.09, 0.1, 0), EYE, (0.04, 0.11, 0.03), "wood_dark")


def bracket(bone, name, p, side):
    """Iron wall bracket carrying a lantern: a plate on the wall, a shelf under the lantern, a brace.
    p: the lantern's base; side: +1 lantern by the port wall, -1 by the starboard wall."""
    p = v3(*p)
    wall = p + v3(side * 0.18, 0, 0)
    add_cube(bone, "lit_" + name + "_plate", wall + v3(0, 0.05, 0), EYE, (0.03, 0.4, 0.14), "iron")
    add_cube(bone, "lit_" + name + "_shelf", p + v3(side * 0.06, -0.015, 0), EYE, (0.3, 0.03, 0.2), "iron")
    beam(bone, "lit_" + name + "_brace", wall + v3(0, -0.2, 0), p + v3(side * 0.02, -0.03, 0), 0.03, "iron")


def pillar(bone, name, p, top):
    """Hold pillar (panel 4): a square oak post on a stone footing, a cap under the beam, two iron bands."""
    p = v3(*p)
    add_cube(bone, "lit_" + name + "_footing", p + v3(0, 0.2, 0), EYE, (0.46, 0.4, 0.46), "wall_stone")
    h = top - p[1] - 0.4
    add_cube(bone, "lit_" + name, p + v3(0, 0.4 + h / 2, 0), EYE, (0.3, h, 0.3), "mast")
    add_cube(bone, "lit_" + name + "_cap", p + v3(0, top - p[1] - 0.08, 0), EYE, (0.42, 0.16, 0.42), "wood_dark")
    for k, t in enumerate((0.3, 0.75)):
        add_cube(bone, "lit_%s_band_%d" % (name, k), p + v3(0, 0.4 + h * t, 0), EYE, (0.32, 0.05, 0.32), "iron")


def coil(bone, name, p, r=0.32):
    sd.rope_coil(gg, bone, name, p, r=r, rope="rope", turns=3)


def post(bone, name, p, top, side):
    """Post against a wall of the coursive, under a deck beam, with a knee at the top."""
    p = v3(*p)
    h = top - p[1]
    add_cube(bone, "lit_" + name, p + v3(0, h / 2, 0), EYE, (0.12, h, 0.24), "wood_dark")
    add_cube(bone, "lit_" + name + "_knee", p + v3(-side * 0.05, h - 0.25, 0), EYE, (0.14, 0.3, 0.2), "wood_dark")


def _bunk(bone, name, p, l, w, blanket):
    add_cube(bone, "lit_" + name + "_frame", p + v3(0, 0.2, 0), EYE, (w, 0.16, l), "wood_dark")
    add_cube(bone, "lit_" + name + "_mattress", p + v3(0, 0.33, 0), EYE, (w - 0.1, 0.12, l - 0.1), "canvas")
    add_cube(bone, "lit_" + name + "_blanket", p + v3(0, 0.41, 0.2), EYE, (w - 0.08, 0.06, l - 0.55), {"all": blanket}, stretch=True)
    add_cube(bone, "lit_" + name + "_pillow", p + v3(0, 0.44, -l / 2 + 0.28), EYE, (w - 0.3, 0.12, 0.32), "linen")
    add_cube(bone, "lit_" + name + "_rail", p + v3(-np.sign(p[0]) * (w / 2 - 0.03), 0.38, 0), EYE, (0.06, 0.14, l - 0.2), "wood_mid")


def bunk2(bone, name, p, l=1.9, w=1.0):
    """Double crew bunk against the hull: two berths on four corner posts, a ladder at the foot."""
    p = v3(*p)
    _bunk(bone, name + "_low", p, l, w, "cloth_roll")
    _bunk(bone, name + "_up", p + v3(0, 1.2, 0), l, w, "bedding")
    for k, (sx, sz) in enumerate(((1, -1), (-1, -1), (1, 1), (-1, 1))):
        q = p + v3(sx * (w / 2 - 0.05), 0, sz * (l / 2 - 0.05))
        add_cube(bone, "lit_%s_post_%d" % (name, k), q + v3(0, 1.2, 0), EYE, (0.1, 2.4, 0.1), "wood_dark")
    add_cube(bone, "lit_" + name + "_head", p + v3(0, 1.2, -l / 2 + 0.03), EYE, (w - 0.1, 2.2, 0.05), "wood_mid")
    for k in range(4):
        beam(bone, "lit_%s_rung_%d" % (name, k), p + v3(-np.sign(p[0]) * (w / 2 - 0.05), 0.55 + 0.3 * k, l / 2 - 0.05),
             p + v3(-np.sign(p[0]) * (w / 2 - 0.05), 0.55 + 0.3 * k, l / 2 - 0.45), 0.05, "wood_mid")


def hammock(bone, name, a, b, sag=0.6, width=0.8, n=8):
    """Canvas hammock slung between two hooks under the beams."""
    a, b = v3(*a), v3(*b)
    d = b - a
    side = norm(np.cross(d, v3(0, 1, 0)))
    pts = [a + d * (t / n) - v3(0, sag * 4 * (t / n) * (1 - t / n), 0) for t in range(n + 1)]
    inner = pts[1:-1]
    for k in range(len(inner) - 1):
        beam(bone, "lit_%s_cloth_%d" % (name, k), inner[k], inner[k + 1], 0.03, "canvas", width=width, up=v3(0, 1, 0), extend=0.01)
    for k, (end, q) in enumerate(((a, inner[0]), (b, inner[-1]))):
        for s in (1, -1):
            beam(bone, "lit_%s_rope_%d_%d" % (name, k, s > 0), end, q + side * s * width * 0.45, 0.025, "rope")
        add_cube(bone, "lit_%s_hook_%d" % (name, k), end + v3(0, 0.05, 0), EYE, (0.06, 0.1, 0.06), "iron")


def pot_rack(bone, name, p, l=1.4):
    """Iron rail hung from the beams over the work table: pans, pots and a ladle on hooks."""
    p = v3(*p)
    y = p[1] - 0.4
    for s in (1, -1):
        beam(bone, "lit_%s_hanger_%d" % (name, s > 0), p + v3(0, 0, s * l / 2), v3(p[0], y, p[2] + s * l / 2), 0.03, "iron")
    beam(bone, "lit_" + name + "_rail", v3(p[0], y, p[2] - l / 2 - 0.05), v3(p[0], y, p[2] + l / 2 + 0.05), 0.05, "iron")
    for k, dz in enumerate(np.linspace(-l / 2 + 0.15, l / 2 - 0.15, 5)):
        q = v3(p[0], y, p[2] + dz)
        beam(bone, "lit_%s_hook_%d" % (name, k), q, q - v3(0, 0.12, 0), 0.02, "iron")
        if k % 2 == 0:
            disc(bone, "lit_%s_pan_%d" % (name, k), q - v3(0, 0.32, 0), (1, 0, 0), 0.16, 0.035, "iron")
            beam(bone, "lit_%s_pan_handle_%d" % (name, k), q - v3(0, 0.12, 0), q - v3(0, 0.17, 0), 0.03, "iron")
        elif k == 1:
            disc(bone, "lit_%s_pot_%d" % (name, k), q - v3(0, 0.27, 0), (0, 1, 0), 0.13, 0.18, "iron")
        else:
            beam(bone, "lit_%s_ladle_%d" % (name, k), q - v3(0, 0.12, 0), q - v3(0, 0.42, 0), 0.025, "bronze")
            disc(bone, "lit_%s_ladle_bowl_%d" % (name, k), q - v3(0, 0.45, 0), (0, 1, 0), 0.06, 0.05, "bronze")


def hams(bone, name, x0, x1, y, z, n=3):
    """Hams and strings of sausages hanging from a beam (kitchen panel)."""
    for k, x in enumerate(np.linspace(x0, x1, n)):
        beam(bone, "lit_%s_string_%d" % (name, k), v3(x, y, z), v3(x, y - 0.3, z), 0.025, "rope")
        if k % 2 == 0:
            add_cube(bone, "lit_%s_ham_%d" % (name, k), v3(x, y - 0.52, z), EYE, (0.22, 0.44, 0.18), "ham")
        else:
            for j in range(3):
                add_cube(bone, "lit_%s_sausage_%d_%d" % (name, k, j), v3(x + 0.07 * (j - 1), y - 0.42 - 0.04 * (j % 2), z), EYE,
                         (0.06, 0.24, 0.06), "ham")
