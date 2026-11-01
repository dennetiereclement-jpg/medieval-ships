"""Furniture made for the Crystal Airship, where none of the user's decoration mods has the piece (tools/crystal_decor.py
places them, tools/generate_crystal.py builds them into the model). All of it is in the second texture (rooms), lit by
the airship's lamps ("lit_" names); the crystals glow ("glow_" names).

  instrument_column  brass column of the cockpit (fluted shaft, collars, a dial, a small globe or a crystal on top)
  crystal_lamp       a brass stand holding a glowing blue crystal (cockpit, engine room)
  wall_gauge         a big brass clock / gauge on a wall
  world_map          the lounge's framed map
  hanging_chain      chains hanging from the storeroom's ceiling, a hook at the end
  speaking_tube      a brass speaking tube from the floor up the wall, its mouth
  floor_grate        an iron floor grate in a riveted brass frame (engine room)
  ceiling_beam       a squared ceiling beam across the room, plain or carved with a gilded running scroll (lounge)
  wall_post          a timber post against a wall, brass collars (cockpit, storeroom, engine room)
  curio_frame        the carved surround of the lounge's curio wall (pilasters, cornice, arched crest, back panel)
  brass_rail         a polished brass guard rail on turned posts (in front of the engine)
  side_machine       a smaller brass machine on its bed: a horizontal drum, flanges, a flywheel, a piston (engine room)
  instrument_column  (top="clock": a big brass chronometer; top="gem": a green glass dome on a cup)
  plump_sack         a lumpy burlap sack, bulging, gathered and tied at the neck (storeroom)
  armchair           a tufted red velvet armchair on a carved dark frame with gilded beads (the lounge's sofas' match)
"""
import math

import numpy as np

import generate_galley as gg
import generate_airship as ga
import leviathan_furniture as lf

v3, norm, add_cube, beam = gg.v3, gg.norm, gg.add_cube, gg.beam
tube, disc, ring, polyline = ga.tube, ga.disc, ga.ring, ga.polyline
box, frame = lf.box, lf.frame
EYE = np.eye(3)


def dial(bone, name, c, normal, r, face="in_gauge", rim="in_brass", depth=0.06, sides=12, lift=0.11):
    """A round instrument like generate_airship.dial, its painted face held further out in front of the rim: the
    z-fighting pass (tools/zfight.py) pushes the rim's coplanar boxes out by up to ~0.1 block, which would cover a
    face set only 0.03 in front of it."""
    n = norm(v3(*normal))
    c = v3(*c)
    disc(bone, name + "_rim", c, n, r, depth, rim, sides=sides)
    add_cube(bone, name, c + n * (depth / 2 + lift), ga.face_frame(n), (1.9 * r, 1.9 * r, 0.012), {"all": None, "+3": face, "-3": face},
             stretch=True)


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
        dial(bone, "lit_%s_dial" % name, top_c + v3(0, 0.22, 0) + n * 0.05, n, 0.22, face="in_gauge", rim="in_brass", depth=0.08)
        box(bone, "lit_%s_dial_back" % name, top_c + v3(0, 0.2, 0), (0.42, 0.42, 0.12), "in_brass_pol")
    elif top == "globe":
        disc(bone, "lit_%s_cup" % name, top_c + v3(0, 0.03, 0), (0, 1, 0), 0.18, 0.06, "in_gold", sides=8)
        for k, (dy, r) in enumerate(((0.1, 0.16), (0.2, 0.22), (0.3, 0.22), (0.4, 0.16))):
            disc(bone, "lit_%s_globe%d" % (name, k), top_c + v3(0, dy + 0.02, 0), (0, 1, 0), r, 0.1, "in_globe", sides=10)
        ring(bone, "lit_%s_meridian" % name, top_c + v3(0, 0.27, 0), (1, 0, 0), 0.27, 0.03, "in_brass", n=10)
    elif top == "clock":
        # a big brass chronometer leaning back on a cradle, facing the helmsman
        c = top_c + v3(0, 0.42, 0) + n * 0.02
        box(bone, "lit_%s_cradle" % name, top_c + v3(0, 0.08, 0), (0.5, 0.16, 0.36), "in_brass_pol")
        disc(bone, "lit_%s_case" % name, c, n, 0.42, 0.16, "in_brass_pol", sides=16)
        ring(bone, "lit_%s_bezel" % name, c + n * 0.09, n, 0.42, 0.07, "in_gold", n=16)
        dial(bone, "lit_%s_face" % name, c + n * 0.06, n, 0.36, face="in_gauge", rim="in_gold", depth=0.05, sides=16, lift=0.16)
        disc(bone, "lit_%s_crown" % name, c + v3(0, 0.47, 0), (0, 1, 0), 0.07, 0.1, "in_gold", sides=6)
    elif top == "gem":
        disc(bone, "lit_%s_cup" % name, top_c + v3(0, 0.04, 0), (0, 1, 0), 0.24, 0.08, "in_gold", sides=8)
        for k, (dy, r) in enumerate(((0.1, 0.17), (0.2, 0.15), (0.28, 0.1))):
            disc(bone, "glow_%s_gem%d" % (name, k), top_c + v3(0, dy, 0), (0, 1, 0), r, 0.09, "in_glass_green", sides=8)
        ring(bone, "lit_%s_cage" % name, top_c + v3(0, 0.16, 0), (0, 1, 0), 0.19, 0.03, "in_brass", n=8)
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
    dial(bone, "lit_%s" % name, c + n * 0.1, n, r, face="in_gauge", rim="in_brass_pol", depth=0.08, sides=16, lift=0.12)
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


def floor_grate(bone, name, p, w=1.0, l=1.0, yaw=0.0):
    """An iron floor grate in a riveted brass frame, laid on the floor at p (its centre)."""
    p = v3(*p)
    R = gg.ry(yaw) if hasattr(gg, "ry") else lf.ry(yaw)
    add_cube(bone, "lit_%s" % name, p + v3(0, 0.012, 0), R, (w, 0.024, l), {"all": "in_brass", "+2": "in_grate_iron"}, stretch=True,
             u_dir=R @ v3(1, 0, 0), v_dir=R @ v3(0, 0, 1))


def ceiling_beam(bone, name, x0, x1, y, z, w=0.3, h=0.3, carved=False, along="x"):
    """A squared beam under the ceiling (its top at y) across the room from x0 to x1 at z (along="z": from x0 to x1 in z
    at x = z). Carved: its sides carry the gilded running scroll, its soffit a gilded bead."""
    if along == "x":
        c, size = v3((x0 + x1) / 2, y - h / 2, z), (x1 - x0, h, w)
        sides = ("+3", "-3")
        ud = v3(1, 0, 0)
    else:
        c, size = v3(z, y - h / 2, (x0 + x1) / 2), (w, h, x1 - x0)
        sides = ("+1", "-1")
        ud = v3(0, 0, 1)
    if not carved:
        add_cube(bone, "lit_%s" % name, c, EYE, size, "in_beam", u_dir=ud, v_dir=v3(0, -1, 0))
        return
    # carved: in lengths of about four blocks, so that the running scroll keeps its scale
    L = x1 - x0
    n = max(1, int(math.ceil(L / 4.0 - 1e-6)))
    reg = {"all": "in_sofa_wood", sides[0]: "in_frieze_gold", sides[1]: "in_frieze_gold", "-2": "in_wood_carved"}
    for k in range(n):
        a = x0 + L * k / n
        b = x0 + L * (k + 1) / n
        if along == "x":
            cc, sz = v3((a + b) / 2, y - h / 2, z), (b - a, h, w)
        else:
            cc, sz = v3(z, y - h / 2, (a + b) / 2), (w, h, b - a)
        add_cube(bone, "lit_%s_%d" % (name, k), cc, EYE, sz, reg, stretch=True, u_dir=ud, v_dir=v3(0, -1, 0))


def wall_post(bone, name, p, h, normal, w=0.3, d=0.2, collars=False, region="in_beam"):
    """A timber post standing against a wall (p: middle of its foot on the wall's face), brass collars if asked."""
    R, u, n = frame(normal)
    p = v3(*p)
    box(bone, "lit_%s" % name, p + n * (d / 2) + v3(0, h / 2, 0), (w, h, d), region, R=R)
    if collars:
        for k, y in enumerate((0.25, h - 0.3)):
            box(bone, "lit_%s_collar%d" % (name, k), p + n * (d / 2) + v3(0, y, 0), (w + 0.05, 0.08, d + 0.05), "in_brass", R=R)


def curio_frame(bone, name, p, normal, w, h, crest=True):
    """The carved surround of a built-in curio wall (p: middle of its foot on the wall's face): a back panel, two
    pilasters with gilded capitals, a cornice with the gilded running scroll and an arched crest with a gilded boss."""
    R, u, n = frame(normal)
    p = v3(*p)
    add_cube(bone, "lit_%s_back" % name, p + n * 0.03 + v3(0, h / 2, 0), R, (w, h, 0.04), {"all": "in_sofa_wood", "+3": "in_panel_carved"},
             stretch=True, u_dir=u, v_dir=v3(0, -1, 0))
    for e in (-1, 1):
        q = p + u * e * (w / 2 + 0.1)
        box(bone, "lit_%s_pil%d" % (name, e > 0), q + n * 0.12 + v3(0, h / 2, 0), (0.22, h, 0.24), "in_wood_carved", R=R)
        box(bone, "lit_%s_cap%d" % (name, e > 0), q + n * 0.14 + v3(0, h - 0.06, 0), (0.3, 0.12, 0.3), "in_gold", R=R)
        box(bone, "lit_%s_base%d" % (name, e > 0), q + n * 0.14 + v3(0, 0.06, 0), (0.3, 0.12, 0.3), "in_sofa_wood", R=R)
    add_cube(bone, "lit_%s_cornice" % name, p + n * 0.16 + v3(0, h + 0.1, 0), R, (w + 0.6, 0.2, 0.32),
             {"all": "in_sofa_wood", "+3": "in_frieze_gold", "-2": "in_gold"}, stretch=True, u_dir=u, v_dir=v3(0, -1, 0))
    if crest:
        for k in range(7):
            a0, a1 = math.pi * k / 7, math.pi * (k + 1) / 7
            r = w * 0.32
            q0 = p + v3(0, h + 0.2, 0) + n * 0.1 + (u * math.cos(a0) + v3(0, 0.55, 0) * math.sin(a0)) * r
            q1 = p + v3(0, h + 0.2, 0) + n * 0.1 + (u * math.cos(a1) + v3(0, 0.55, 0) * math.sin(a1)) * r
            beam(bone, "lit_%s_crest%d" % (name, k), q0, q1, 0.1, "in_gold", width=0.08, up=n, extend=0.03)
        disc(bone, "lit_%s_boss" % name, p + v3(0, h + 0.38, 0) + n * 0.12, n, 0.12, 0.06, "in_gold", sides=8)


def brass_rail(bone, name, pts, h=1.0, step=0.6):
    """A polished brass guard rail on turned posts along a polyline of foot points."""
    pts = [v3(*q) for q in pts]
    for k in range(len(pts) - 1):
        a, b = pts[k], pts[k + 1]
        L = np.linalg.norm(b - a)
        if L < 1e-3:
            continue
        tube(bone, "lit_%s_rail%d" % (name, k), a + v3(0, h, 0), b + v3(0, h, 0), 0.1, "in_brass_pol", sides=6, extend=0.05)
        tube(bone, "lit_%s_mid%d" % (name, k), a + v3(0, h * 0.5, 0), b + v3(0, h * 0.5, 0), 0.06, "in_brass", sides=6)
        nn = max(1, int(round(L / step)))
        for j in range(nn + (1 if k == len(pts) - 2 else 0)):
            q = a + (b - a) * j / nn
            tube(bone, "lit_%s_post%d_%d" % (name, k, j), q, q + v3(0, h, 0), 0.08, "in_brass_pol", sides=6)
            disc(bone, "lit_%s_knob%d_%d" % (name, k, j), q + v3(0, h + 0.05, 0), (0, 1, 0), 0.07, 0.08, "in_gold", sides=6)
            disc(bone, "lit_%s_foot%d_%d" % (name, k, j), q + v3(0, 0.03, 0), (0, 1, 0), 0.08, 0.06, "in_brass", sides=6)


def side_machine(bone, name, p, axis=(1, 0, 0), length=1.6, r=0.38, h=0.75):
    """A smaller brass machine on its iron bed (p: middle of its foot): a horizontal riveted drum along axis with gilded
    bands and flanges, a flywheel at one end, a piston and a gauge on top, a pipe up."""
    p = v3(*p)
    a = norm(v3(*axis))
    side = np.cross(v3(0, 1, 0), a)
    c = p + v3(0, h, 0)
    box(bone, "lit_%s_bed" % name, p + v3(0, 0.15, 0), (length + 0.2, 0.3, 2 * r + 0.2), "in_rivets",
        R=np.column_stack([a, v3(0, 1, 0), side]))
    for e in (-1, 1):
        box(bone, "lit_%s_saddle%d" % (name, e > 0), p + a * e * length * 0.3 + v3(0, (0.3 + h - r * 0.6) / 2, 0),
            (0.16, h - r * 0.6 - 0.3 + 0.1, 2 * r * 0.8), "in_iron", R=np.column_stack([a, v3(0, 1, 0), side]))
    tube(bone, "lit_%s_drum" % name, c - a * length / 2, c + a * length / 2, 2 * r, "in_boiler", sides=10)
    for k, t in enumerate((-0.45, 0.0, 0.45)):
        tube(bone, "lit_%s_band%d" % (name, k), c + a * (t * length - 0.05), c + a * (t * length + 0.05), 2 * r + 0.08, "in_gold", sides=10)
    tube(bone, "lit_%s_flange" % name, c + a * (length / 2), c + a * (length / 2 + 0.08), 2 * r + 0.16, "in_brass_pol", sides=10)
    tube(bone, "lit_%s_shaft" % name, c + a * (length / 2), c + a * (length / 2 + 0.35), 0.14, "in_iron", sides=6)
    lf.gear(bone, "lit_%s_fly" % name, c + a * (length / 2 + 0.3), a, r * 1.15, 0.1, teeth=14, region="in_brass", spokes=5)
    tube(bone, "lit_%s_cyl" % name, c + v3(0, r * 0.8, 0) - a * 0.3, c + v3(0, r + 0.45, 0) - a * 0.3, 0.3, "in_copper", sides=8)
    box(bone, "lit_%s_head" % name, c + v3(0, r + 0.5, 0) - a * 0.3, (0.34, 0.1, 0.34), "in_brass_pol")
    dial(bone, "lit_%s_gauge" % name, c + v3(0, r + 0.2, 0) + a * 0.35 + v3(0, 0.05, 0), side,
            0.13, face="in_gauge", rim="in_brass", depth=0.05, sides=10)


def armchair(bone, name, p, facing, w=0.9, d=0.85):
    """A tufted red velvet armchair (the lounge's, matching the Farmhouse sofas of the sheet): a carved dark wooden
    frame on turned feet, a deep seat cushion, a high rounded back, rolled arms with gilded beads (p: middle of its foot,
    facing: where the sitter looks)."""
    R = lf.yaw_r(facing)
    p = v3(*p)
    fx, up, fz = R @ v3(1, 0, 0), v3(0, 1, 0), R @ v3(0, 0, 1)
    for ex in (-1, 1):
        for ez in (-1, 1):
            q = p + fx * ex * (w / 2 - 0.1) + fz * ez * (d / 2 - 0.1)
            tube(bone, "lit_%s_foot_%d%d" % (name, ex > 0, ez > 0), q, q + up * 0.14, 0.09, "in_sofa_wood", sides=6)
    box(bone, "lit_%s_base" % name, p + up * 0.2, (w, 0.14, d), "in_sofa_wood", R=R)
    box(bone, "lit_%s_seat" % name, p + up * 0.36 + fz * 0.05, (w - 0.24, 0.18, d - 0.2), "in_sofa", R=R)
    box(bone, "lit_%s_back" % name, p + up * 0.68 - fz * (d / 2 - 0.1), (w - 0.06, 0.82, 0.2), "in_sofa", R=R)
    box(bone, "lit_%s_back_top" % name, p + up * 1.1 - fz * (d / 2 - 0.1), (w - 0.2, 0.08, 0.22), "in_sofa", R=R)
    box(bone, "lit_%s_back_frame" % name, p + up * 0.62 - fz * (d / 2 - 0.02), (w, 0.9, 0.06), "in_sofa_wood", R=R)
    for ex in (-1, 1):
        box(bone, "lit_%s_arm_%d" % (name, ex > 0), p + fx * ex * (w / 2 - 0.07) + up * 0.5, (0.14, 0.32, d - 0.08), "in_sofa", R=R)
        box(bone, "lit_%s_armroll_%d" % (name, ex > 0), p + fx * ex * (w / 2 - 0.07) + up * 0.68 + fz * 0.02, (0.18, 0.06, d - 0.04), "in_sofa_wood",
            R=R)
        box(bone, "lit_%s_bead_%d" % (name, ex > 0), p + fx * ex * (w / 2 - 0.07) + up * 0.715 + fz * 0.02, (0.06, 0.02, d - 0.08), "in_gold",
            R=R)


def helm_dais(bone, name, p, r=0.75, h=0.1):
    """A low round dais of polished planks with a brass edge under the helm's pedestal."""
    p = v3(*p)
    disc(bone, "lit_%s" % name, p + v3(0, h / 2, 0), (0, 1, 0), r, h, "in_floor_capt", sides=12)
    ring(bone, "lit_%s_edge" % name, p + v3(0, h - 0.02, 0), (0, 1, 0), r + 0.02, 0.05, "in_brass_pol", n=12)


def plump_sack(bone, name, p, yaw=0.0, s=1.0):
    """A lumpy burlap sack of grain or flour: a bulging body in three tiers, a gathered neck, a tuft and a rope tie."""
    p = v3(*p)
    R = lf.ry(yaw)
    for k, (y0, y1, w, d) in enumerate(((0.0, 0.18, 0.56, 0.46), (0.18, 0.44, 0.64, 0.52), (0.44, 0.6, 0.52, 0.42), (0.6, 0.68, 0.34, 0.28))):
        box(bone, "lit_%s_body%d" % (name, k), p + v3(0, (y0 + y1) / 2 * s, 0), (w * s, (y1 - y0) * s, d * s), "in_cloth_sack", R=R @ lf.ry(0.12 * k))
    box(bone, "lit_%s_neck" % name, p + v3(0, 0.74 * s, 0), (0.18 * s, 0.12 * s, 0.16 * s), "in_cloth_sack", R=R)
    box(bone, "lit_%s_tie" % name, p + v3(0, 0.74 * s, 0), (0.21 * s, 0.05 * s, 0.19 * s), "in_rope", R=R)
    box(bone, "lit_%s_tuft" % name, p + v3(0, 0.84 * s, 0), (0.28 * s, 0.09 * s, 0.22 * s), "in_cloth_sack", R=R @ lf.ry(0.6))
