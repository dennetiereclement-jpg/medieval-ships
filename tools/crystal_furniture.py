"""Furniture made for the Crystal Airship, where none of the user's decoration mods has the piece (tools/crystal_decor.py
places them, tools/generate_crystal.py builds them into the model). All of it is in the second texture (rooms), lit by
the airship's lamps ("lit_" names); the crystals glow ("glow_" names).

  instrument_column  brass column of the cockpit (fluted shaft, collars, a dial, a small globe or a crystal on top)
  crystal_lamp       a brass stand holding a glowing blue crystal (cockpit, engine room)
  wall_gauge         a big brass clock / gauge on a wall
  world_map          the lounge's framed map
  hanging_chain      chains hanging from the storeroom's ceiling, a hook at the end
  speaking_tube      a brass speaking tube from the floor up the wall, its mouth
"""
import math

import numpy as np

import generate_galley as gg
import generate_airship as ga
import leviathan_furniture as lf

v3, norm, add_cube, beam = gg.v3, gg.norm, gg.add_cube, gg.beam
tube, disc, ring, polyline = ga.tube, ga.disc, ga.ring, ga.polyline
box, frame = lf.box, lf.frame


def crystal(bone, name, base, d, length, r, sides=6):
    """A glowing crystal: a prism along d from base, ending in a point."""
    base, d = v3(*base), norm(v3(*d))
    tube(bone, "glow_" + name, base, base + d * length * 0.68, 2 * r, "in_crystal", sides=sides)
    for k in range(3):
        t0, t1 = 0.66 + 0.11 * k, 0.66 + 0.11 * (k + 1)
        tube(bone, "glow_%s_tip%d" % (name, k), base + d * length * t0, base + d * length * t1, 2 * r * (1 - (k + 0.5) / 3.2), "in_crystal",
             sides=sides)


def instrument_column(bone, name, p, top="dial", h=1.25, facing=(0, 0, 1)):
    p = v3(*p)
    n = norm(v3(*facing))
    tube(bone, "lit_%s_foot" % name, p, p + v3(0, 0.14, 0), 0.62, "in_brass_pol", sides=8)
    tube(bone, "lit_%s_plinth" % name, p + v3(0, 0.14, 0), p + v3(0, 0.3, 0), 0.5, "in_wood_carved", sides=8)
    tube(bone, "lit_%s_shaft" % name, p + v3(0, 0.3, 0), p + v3(0, h - 0.2, 0), 0.32, "in_brass_pol", sides=8)
    for k, y in enumerate((0.45, h * 0.62, h - 0.22)):
        tube(bone, "lit_%s_collar%d" % (name, k), p + v3(0, y - 0.04, 0), p + v3(0, y + 0.04, 0), 0.42, "in_gold", sides=8)
    tube(bone, "lit_%s_cap" % name, p + v3(0, h - 0.2, 0), p + v3(0, h, 0), 0.56, "in_wood_carved", sides=8)
    top_c = p + v3(0, h, 0)
    if top == "dial":
        ga.dial(bone, "lit_%s_dial" % name, top_c + v3(0, 0.22, 0) + n * 0.05, n, 0.22, face="in_gauge", rim="in_brass", depth=0.08)
        box(bone, "lit_%s_dial_back" % name, top_c + v3(0, 0.2, 0), (0.42, 0.42, 0.12), "in_brass_pol")
    elif top == "globe":
        disc(bone, "lit_%s_cup" % name, top_c + v3(0, 0.03, 0), (0, 1, 0), 0.18, 0.06, "in_gold", sides=8)
        for k, (dy, r) in enumerate(((0.1, 0.16), (0.2, 0.22), (0.3, 0.22), (0.4, 0.16))):
            disc(bone, "lit_%s_globe%d" % (name, k), top_c + v3(0, dy + 0.02, 0), (0, 1, 0), r, 0.1, "in_globe", sides=10)
        ring(bone, "lit_%s_meridian" % name, top_c + v3(0, 0.27, 0), (1, 0, 0), 0.27, 0.03, "in_brass", n=10)
    else:
        disc(bone, "lit_%s_cup" % name, top_c + v3(0, 0.03, 0), (0, 1, 0), 0.22, 0.08, "in_gold", sides=8)
        crystal(bone, "%s_crystal" % name, top_c + v3(0, 0.05, 0), (0, 1, 0), 0.5, 0.12)


def crystal_lamp(bone, name, p, h=1.4, r=0.18):
    """A brass stand with three claws holding a glowing blue crystal."""
    p = v3(*p)
    tube(bone, "lit_%s_foot" % name, p, p + v3(0, 0.1, 0), 0.5, "in_brass_pol", sides=8)
    tube(bone, "lit_%s_stem" % name, p + v3(0, 0.1, 0), p + v3(0, h, 0), 0.12, "in_brass_pol", sides=6)
    disc(bone, "lit_%s_cup" % name, p + v3(0, h, 0), (0, 1, 0), 0.24, 0.08, "in_gold", sides=8)
    crystal(bone, "%s_crystal" % name, p + v3(0, h, 0), (0, 1, 0), 0.7, r)
    for k in range(3):
        a = 2 * math.pi * k / 3
        tube(bone, "lit_%s_claw%d" % (name, k), p + v3(0, h, 0), p + v3(math.cos(a) * 0.22, h + 0.4, math.sin(a) * 0.22), 0.04, "in_gold", sides=4)


def wall_gauge(bone, name, center, normal, r=0.5):
    R, u, n = frame(normal)
    c = v3(*center)
    disc(bone, "lit_%s_back" % name, c + n * 0.04, n, r + 0.1, 0.08, "in_wood_carved", sides=16)
    ga.dial(bone, "lit_%s" % name, c + n * 0.1, n, r, face="in_gauge", rim="in_brass_pol", depth=0.08, sides=16)
    ring(bone, "lit_%s_bezel" % name, c + n * 0.14, n, r + 0.02, 0.06, "in_gold", n=16)
    for k in range(4):
        a = math.pi / 2 * k + math.pi / 4
        d = u * math.cos(a) + v3(0, 1, 0) * math.sin(a)
        box(bone, "lit_%s_bolt%d" % (name, k), c + d * (r + 0.1) + n * 0.1, (0.07, 0.07, 0.05), "in_gold", R=R)


def world_map(bone, name, center, normal, w=1.6, h=1.05):
    R, u, n = frame(normal)
    c = v3(*center)
    add_cube(bone, "lit_%s" % name, c + n * 0.03, R, (w, h, 0.02), {"all": None, "+3": "in_map_world"}, stretch=True, u_dir=u, v_dir=v3(0, -1, 0))
    for e in (-1, 1):
        box(bone, "lit_%s_v%d" % (name, e > 0), c + u * e * (w / 2 + 0.05) + n * 0.05, (0.1, h + 0.2, 0.06), "in_wood_carved", R=R)
        box(bone, "lit_%s_h%d" % (name, e > 0), c + v3(0, e * (h / 2 + 0.05), 0) + n * 0.05, (w + 0.2, 0.1, 0.06), "in_wood_carved", R=R)


def hanging_chain(bone, name, top, length, hook=True):
    top = v3(*top)
    n = max(2, int(length / 0.2))
    for k in range(n):
        c = top - v3(0, (k + 0.5) * length / n, 0)
        R = gg.ry(math.pi / 2 * (k % 2)) if hasattr(gg, "ry") else np.eye(3)
        add_cube(bone, "lit_%s_%d" % (name, k), c, R, (0.1, length / n + 0.04, 0.035), "in_iron")
    if hook:
        b = top - v3(0, length, 0)
        beam(bone, "lit_%s_hook_a" % name, b, b - v3(0, 0.14, 0), 0.04, "in_iron")
        beam(bone, "lit_%s_hook_b" % name, b - v3(0, 0.14, 0), b - v3(-0.1, 0.1, 0), 0.04, "in_iron")


def speaking_tube(bone, name, foot, top, normal):
    foot, top = v3(*foot), v3(*top)
    n = norm(v3(*normal))
    tube(bone, "lit_%s_pipe" % name, foot, top, 0.12, "in_brass_pol", sides=6)
    tube(bone, "lit_%s_bend" % name, top, top + n * 0.25, 0.12, "in_brass_pol", sides=6)
    tube(bone, "lit_%s_mouth" % name, top + n * 0.2, top + n * 0.34, 0.26, "in_gold", sides=8)
