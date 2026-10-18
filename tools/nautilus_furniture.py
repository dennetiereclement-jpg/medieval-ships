"""Furniture made for the Nautilus: what the decoration mods do not have (or not close enough to the
reference sheet): the monumental organ, the showcases' corals and shells, chandeliers, gilded
paintings, Chesterfield sofas, the globe, Nemo's iron bed and instruments, the wheelhouse fittings,
the projector, the batteries, the engine, the diving suits, the lifeboat.

Every function takes the bone, a name prefix and its placement (ship-local blocks). Element names
start with "lit" (lit by the Nautilus's lamps) or "glow" (full bright).
"""
import math

import numpy as np

import generate_galley as gg

v3, norm, add_cube, beam = gg.v3, gg.norm, gg.add_cube, gg.beam
EYE = np.eye(3)


def ry(a):
    return gg.ry(a)


def frame(normal):
    """Axes (u, up, n) of a wall-mounted item facing `normal` (horizontal)."""
    n = norm(v3(normal[0], 0, normal[2]))
    u = np.cross(v3(0, 1, 0), n)
    return np.column_stack([u, v3(0, 1, 0), n]), u, n


def yaw_of(facing):
    """Facing direction name -> rotation about y (radians) of an object whose front looks along +z."""
    return {"bow": 0.0, "port": math.pi / 2, "stern": math.pi, "starboard": -math.pi / 2}[facing]


def box(bone, name, c, R, size, region):
    return add_cube(bone, "lit_" + name, c, R, size, region)


# ---------------------------------------------------------------- lights, paintings
def chandelier(bone, name, hook, r=0.7, n=10, drop=0.7, tiers=2):
    """Gilded electric chandelier: rod, a boss, one or two rings of arms ending in lit globes."""
    hook = v3(*hook)
    c = hook - v3(0, drop, 0)
    box(bone, name + "_rod", (hook + c) / 2, EYE, (0.05, drop, 0.05), "gold")
    box(bone, name + "_boss", c, EYE, (0.24, 0.3, 0.24), "gold")
    box(bone, name + "_drop", c - v3(0, 0.3, 0), EYE, (0.1, 0.22, 0.1), "gold")
    for t in range(tiers):
        rr, y, k_n = r * (1 - 0.35 * t), -0.1 + 0.28 * t, n - 3 * t
        for k in range(k_n):
            a0, a1 = 2 * math.pi * k / k_n, 2 * math.pi * (k + 1) / k_n
            p0 = c + v3(math.cos(a0) * rr, y, math.sin(a0) * rr)
            p1 = c + v3(math.cos(a1) * rr, y, math.sin(a1) * rr)
            beam(bone, "lit_%s_ring%d_%d" % (name, t, k), p0, p1, 0.04, "gold", extend=0.02)
            beam(bone, "lit_%s_arm%d_%d" % (name, t, k), c + v3(0, y - 0.05, 0), p0, 0.035, "gold")
            add_cube(bone, "lit_%s_cup%d_%d" % (name, t, k), p0 + v3(0, 0.03, 0), EYE, (0.09, 0.05, 0.09), "gold")
            add_cube(bone, "glow_%s_bulb%d_%d" % (name, t, k), p0 + v3(0, 0.12, 0), EYE, (0.08, 0.12, 0.08), "glow")


def wall_lamp(bone, name, p, normal):
    """Brass sconce with a lit globe."""
    R, u, n = frame(normal)
    p = v3(*p)
    box(bone, name + "_plate", p + n * 0.02, R, (0.18, 0.28, 0.04), "brass")
    beam(bone, "lit_" + name + "_arm", p + n * 0.03, p + n * 0.22 + v3(0, 0.08, 0), 0.04, "brass")
    add_cube(bone, "glow_" + name, p + n * 0.24 + v3(0, 0.18, 0), EYE, (0.14, 0.18, 0.14), "glow")


def painting(bone, name, center, normal, w, h, region):
    """Painting in a heavy gilded frame on a wall whose inner side faces `normal`."""
    R, u, n = frame(normal)
    c = v3(*center) + n * 0.04
    add_cube(bone, "lit_" + name, c, R, (w, h, 0.03), {"all": "gold", "+3": region}, stretch=True, u_dir=u, v_dir=v3(0, -1, 0))
    t = 0.12
    for k, (dx, dy, sw, sh) in enumerate(((0, h / 2 + t / 2, w + 2 * t, t), (0, -h / 2 - t / 2, w + 2 * t, t),
                                          (w / 2 + t / 2, 0, t, h), (-w / 2 - t / 2, 0, t, h))):
        box(bone, "%s_frame%d" % (name, k), c + u * dx + v3(0, dy, 0) + n * 0.02, R, (sw, sh, 0.1), "gold")


def drapes(bone, name, center, normal, w, h):
    """Red velvet curtains on each side of a window, with a gilded pelmet."""
    R, u, n = frame(normal)
    c = v3(*center) + n * 0.12
    for s in (-1, 1):
        for k in range(3):
            box(bone, "%s_%d_%d" % (name, s > 0, k), c + u * s * (w / 2 + 0.18 + 0.12 * k) + n * (0.04 * (k % 2)), R,
                (0.14, h, 0.1), "red_velvet")
    box(bone, name + "_pelmet", c + v3(0, h / 2 + 0.12, 0), R, (w + 1.1, 0.26, 0.16), "gold")


# ---------------------------------------------------------------- salon
def organ(bone, name, base, normal, width=5.2, height=5.2):
    """The monumental organ of the grand salon, against a wall (base = middle of its foot on the floor,
    `normal` towards the room): carved case with gilded trims, three tiers of silver pipes rising to
    the centre, a console with two keyboards, a bench."""
    R, u, n = frame(normal)
    b = v3(*base)
    depth = 1.1
    # case
    box(bone, name + "_case", b + v3(0, 1.1, 0) + n * (depth / 2), R, (width, 2.2, depth), "organ_wood")
    box(bone, name + "_case_top", b + v3(0, 2.26, 0) + n * (depth / 2 + 0.03), R, (width + 0.2, 0.16, depth + 0.1), "gold")
    box(bone, name + "_back", b + v3(0, height / 2, 0) + n * 0.15, R, (width, height, 0.3), "organ_wood")
    for s in (-1, 1):
        box(bone, "%s_tower_%d" % (name, s > 0), b + u * s * (width / 2 - 0.35) + v3(0, height / 2, 0) + n * 0.45, R,
            (0.7, height, 0.6), "organ_wood")
        box(bone, "%s_tower_cap_%d" % (name, s > 0), b + u * s * (width / 2 - 0.35) + v3(0, height + 0.08, 0) + n * 0.45, R,
            (0.8, 0.16, 0.7), "gold")
    # pipes: three tiers, tallest in the middle
    for tier, (yb, maxh, dz, step) in enumerate(((2.35, 2.6, 0.75, 0.3), (2.35, 2.2, 0.48, 0.26), (2.6, 1.6, 0.3, 0.22))):
        half = width / 2 - 0.8 - tier * 0.1
        k = 0
        x = -half
        while x <= half + 1e-6:
            f = 1 - abs(x) / (half + 0.01)
            hh = maxh * (0.45 + 0.55 * f ** 0.8)
            c = b + u * x + v3(0, yb + hh / 2, 0) + n * dz
            box(bone, "%s_pipe%d_%d" % (name, tier, k), c, R, (step * 0.8, hh, step * 0.8), "silver")
            box(bone, "%s_mouth%d_%d" % (name, tier, k), c + v3(0, -hh / 2 + 0.25, 0) + n * (step * 0.41), R,
                (step * 0.5, 0.12, 0.02), "iron")
            x += step
            k += 1
    # gilded crest at the top
    box(bone, name + "_crest", b + v3(0, height - 0.1, 0) + n * 0.32, R, (1.6, 0.4, 0.12), "gold")
    # console with two keyboards, a music stand, stops, a bench
    cz = depth + 0.35
    box(bone, name + "_console", b + v3(0, 0.55, 0) + n * cz, R, (2.2, 1.1, 0.7), "organ_wood")
    for k, y in enumerate((0.95, 1.12)):
        add_cube(bone, "lit_%s_keys%d" % (name, k), b + v3(0, y, 0) + n * (cz + 0.3 + 0.12 * (1 - k)), R, (1.8, 0.05, 0.24),
                 {"all": "organ_wood", "+2": "keys"}, stretch=True)
    box(bone, name + "_stand", b + v3(0, 1.45, 0) + n * (cz + 0.05), R, (1.0, 0.5, 0.05), "organ_wood")
    for k in range(6):
        box(bone, "%s_stop%d" % (name, k), b + u * (-0.9 + 0.36 * k) + v3(0, 1.3, 0) + n * (cz + 0.33), R, (0.06, 0.06, 0.1), "wax")
    bench = b + n * (cz + 1.05)
    box(bone, name + "_bench", bench + v3(0, 0.45, 0), R, (1.5, 0.1, 0.4), "organ_wood")
    for s in (-1, 1):
        box(bone, "%s_bench_leg%d" % (name, s > 0), bench + u * s * 0.65 + v3(0, 0.2, 0), R, (0.08, 0.4, 0.34), "organ_wood")


def showcase_contents(bone, name, center, kind):
    """What stands in a showcase: branched corals, shells and pearls (kind 0..3)."""
    c = v3(*center)
    box(bone, name + "_stand", c + v3(0, 0.05, 0), EYE, (0.5, 0.1, 0.5), "organ_wood")
    if kind in (0, 2):
        reg = ("coral_red", "coral_pink", "coral_orange")[kind % 3]
        base = c + v3(0, 0.1, 0)
        branches = [(0, 0.45, 0.0), (0.18, 0.35, 0.1), (-0.15, 0.4, -0.08), (0.08, 0.6, -0.15), (-0.2, 0.3, 0.15)]
        for k, (dx, dy, dz) in enumerate(branches):
            tip = base + v3(dx, dy, dz)
            beam(bone, "lit_%s_coral%d" % (name, k), base + v3(dx * 0.3, 0.05, dz * 0.3), tip, 0.07, reg)
            beam(bone, "lit_%s_twig%d" % (name, k), tip, tip + v3(dx * 0.4 + 0.06, 0.12, dz * 0.4 - 0.05), 0.05, reg)
    else:
        for k, (dx, dz, s) in enumerate(((0, 0, 0.26), (0.18, 0.12, 0.16), (-0.16, -0.1, 0.18))):
            p = c + v3(dx, 0.1 + s / 2, dz)
            box(bone, "%s_shell%d" % (name, k), p, ry(0.6 * k), (s, s * 0.7, s * 1.2), "shell")
            box(bone, "%s_shell%d_rib" % (name, k), p + v3(0, s * 0.36, 0), ry(0.6 * k), (s * 0.3, 0.02, s * 1.1), "coral_orange")
        for k in range(5):
            a = 2 * math.pi * k / 5
            box(bone, "%s_pearl%d" % (name, k), c + v3(math.cos(a) * 0.12, 0.42, math.sin(a) * 0.12), EYE, (0.07, 0.07, 0.07), "pearl")
        box(bone, name + "_pearl_dish", c + v3(0, 0.37, 0), EYE, (0.34, 0.04, 0.34), "gold")


def armchair(bone, name, p, facing, region="red_velvet"):
    """Wing armchair in velvet on gilded feet; the sitter looks along `facing`."""
    R = ry(yaw_of(facing))
    p = v3(*p)
    box(bone, name + "_seat", p + v3(0, 0.38, 0), R, (0.82, 0.22, 0.8), region)
    box(bone, name + "_back", p + R @ v3(0, 0.95, -0.34), R, (0.82, 0.95, 0.16), region)
    for s in (-1, 1):
        box(bone, "%s_arm%d" % (name, s > 0), p + R @ v3(s * 0.38, 0.62, 0.0), R, (0.14, 0.3, 0.8), region)
        box(bone, "%s_wing%d" % (name, s > 0), p + R @ v3(s * 0.36, 1.05, -0.26), R, (0.1, 0.5, 0.3), region)
        for t in (-1, 1):
            box(bone, "%s_foot%d%d" % (name, s > 0, t > 0), p + R @ v3(s * 0.33, 0.13, t * 0.32), R, (0.08, 0.26, 0.08), "gold")


def chesterfield(bone, name, p, facing, length=2.4, region="green_leather"):
    """Tufted leather sofa with rolled arms; the sitters look along `facing`."""
    R = ry(yaw_of(facing))
    p = v3(*p)
    box(bone, name + "_base", p + v3(0, 0.25, 0), R, (length, 0.3, 0.9), region)
    box(bone, name + "_cushion", p + v3(0, 0.46, 0.05), R, (length - 0.5, 0.14, 0.75), region)
    box(bone, name + "_back", p + R @ v3(0, 0.75, -0.36), R, (length, 0.62, 0.2), region)
    for s in (-1, 1):
        box(bone, "%s_arm%d" % (name, s > 0), p + R @ v3(s * (length / 2 - 0.13), 0.6, 0.0), R, (0.26, 0.4, 0.92), region)
        box(bone, "%s_roll%d" % (name, s > 0), p + R @ v3(s * (length / 2 - 0.13), 0.82, 0.0), R, (0.32, 0.1, 0.96), region)
        for t in (-1, 1):
            box(bone, "%s_foot%d%d" % (name, s > 0, t > 0), p + R @ v3(s * (length / 2 - 0.15), 0.05, t * 0.35), R,
                (0.1, 0.1, 0.1), "organ_wood")


def globe(bone, name, p):
    """Terrestrial globe on a turned wooden stand with a brass meridian."""
    p = v3(*p)
    box(bone, name + "_foot", p + v3(0, 0.04, 0), EYE, (0.5, 0.08, 0.5), "organ_wood")
    box(bone, name + "_column", p + v3(0, 0.4, 0), EYE, (0.12, 0.7, 0.12), "organ_wood")
    box(bone, name + "_horizon", p + v3(0, 0.95, 0), EYE, (0.86, 0.06, 0.86), "organ_wood")
    c = p + v3(0, 1.0, 0)
    for k in range(3):
        box(bone, "%s_ball%d" % (name, k), c, ry(k * math.pi / 6) @ gg.rx(0.4), (0.62 - 0.04 * k, 0.62, 0.62 - 0.04 * k), "chart")
    for k in range(10):
        a0, a1 = 2 * math.pi * k / 10, 2 * math.pi * (k + 1) / 10
        beam(bone, "lit_%s_meridian%d" % (name, k), c + v3(0, math.cos(a0) * 0.4, math.sin(a0) * 0.4),
             c + v3(0, math.cos(a1) * 0.4, math.sin(a1) * 0.4), 0.04, "brass")


def tall_bookcase(bone, name, p, normal, w=1.0, h=4.0):
    """Floor to ceiling bookcase (custom: filled with the painted book spines)."""
    R, u, n = frame(normal)
    p = v3(*p)
    add_cube(bone, "lit_" + name, p + v3(0, h / 2, 0) + n * 0.2, R, (w, h, 0.4), {"all": "organ_wood", "+3": "books"},
             stretch=True, u_dir=u, v_dir=v3(0, -1, 0))
    box(bone, name + "_crown", p + v3(0, h - 0.05, 0) + n * 0.24, R, (w + 0.06, 0.1, 0.48), "gold")


def rug(bone, name, p, w, l, region="rug"):
    """Rug lying on the floor."""
    p = v3(*p)
    add_cube(bone, "lit_" + name, p + v3(0, 0.012, 0), EYE, (w, 0.02, l), {"all": None, "+2": region}, stretch=True)


# ---------------------------------------------------------------- Nemo, Aronnax
def iron_bed(bone, name, p, facing, l=2.0, w=1.0):
    R = ry(yaw_of(facing))
    p = v3(*p)
    box(bone, name + "_frame", p + v3(0, 0.35, 0), R, (w, 0.1, l), "steel")
    box(bone, name + "_mattress", p + v3(0, 0.48, 0), R, (w - 0.08, 0.16, l - 0.1), "bedding")
    box(bone, name + "_blanket", p + R @ v3(0, 0.57, 0.25), R, (w - 0.04, 0.04, l - 0.6), "ceil_steel")
    box(bone, name + "_pillow", p + R @ v3(0, 0.6, -l / 2 + 0.3), R, (w - 0.3, 0.1, 0.3), "bedding")
    for t, hh in ((-1, 1.1), (1, 0.8)):
        for s in (-1, 1):
            box(bone, "%s_post%d%d" % (name, t > 0, s > 0), p + R @ v3(s * (w / 2 - 0.04), hh / 2, t * (l / 2 - 0.04)), R,
                (0.07, hh, 0.07), "steel")
        for k, y in enumerate((hh - 0.06, hh * 0.55)):
            box(bone, "%s_rail%d%d" % (name, t > 0, k), p + R @ v3(0, y, t * (l / 2 - 0.04)), R, (w, 0.05, 0.05), "steel")


def instrument_panel(bone, name, center, normal, w=1.6, h=1.2):
    """Riveted board with gauges, thermometers and an electric dial (Nemo's room, the engine room)."""
    R, u, n = frame(normal)
    c = v3(*center) + n * 0.04
    box(bone, name + "_board", c, R, (w, h, 0.06), "steel")
    cols = max(2, int(w / 0.45))
    for i in range(cols):
        for j in range(2):
            p = c + u * (-w / 2 + (i + 0.5) * w / cols) + v3(0, h / 4 - j * h / 2, 0) + n * 0.045
            add_cube(bone, "lit_%s_gauge%d%d" % (name, i, j), p, R, (0.32, 0.32, 0.03), {"all": "brass", "+3": "gauge"}, stretch=True)
    box(bone, name + "_thermo", c + u * (w / 2 + 0.15) + n * 0.05, R, (0.08, h * 0.8, 0.05), "glass")


def ship_wheel(bone, name, center, axis_normal, r=0.65):
    """Wooden ship's wheel with brass hub and rim, eight handles (in its own bone to turn with the helm)."""
    c = v3(*center)
    nrm = norm(v3(*axis_normal))
    e1 = norm(np.cross(nrm, v3(0, 1, 0)))
    e2 = np.cross(nrm, e1)
    for k in range(12):
        a0, a1 = 2 * math.pi * k / 12, 2 * math.pi * (k + 1) / 12
        beam(bone, "lit_%s_rim%d" % (name, k), c + (e1 * math.cos(a0) + e2 * math.sin(a0)) * r,
             c + (e1 * math.cos(a1) + e2 * math.sin(a1)) * r, 0.07, "prop", up=nrm, extend=0.02)
    for k in range(8):
        a = 2 * math.pi * k / 8
        d = e1 * math.cos(a) + e2 * math.sin(a)
        beam(bone, "lit_%s_spoke%d" % (name, k), c, c + d * (r + 0.22), 0.05, "prop")
    add_cube(bone, "lit_%s_hub" % name, c, EYE, (0.18, 0.18, 0.18), "brass")


def binnacle(bone, name, p):
    p = v3(*p)
    box(bone, name + "_column", p + v3(0, 0.5, 0), EYE, (0.34, 1.0, 0.34), "organ_wood")
    box(bone, name + "_bowl", p + v3(0, 1.1, 0), EYE, (0.42, 0.2, 0.42), "brass")
    add_cube(bone, "lit_%s_card" % name, p + v3(0, 1.21, 0), EYE, (0.3, 0.02, 0.3), {"all": "brass", "+2": "gauge"}, stretch=True)
    for s in (-1, 1):
        box(bone, "%s_sphere%d" % (name, s > 0), p + v3(s * 0.32, 1.1, 0), EYE, (0.14, 0.14, 0.14), "steel")


def telegraph(bone, name, p, normal):
    R, u, n = frame(normal)
    p = v3(*p)
    box(bone, name + "_column", p + v3(0, 0.55, 0), R, (0.16, 1.1, 0.16), "brass")
    add_cube(bone, "lit_%s_dial" % name, p + v3(0, 1.2, 0), R, (0.4, 0.4, 0.14), {"all": "brass", "+3": "gauge", "-3": "gauge"}, stretch=True)
    beam(bone, "lit_%s_handle" % name, p + v3(0, 1.2, 0) + n * 0.08, p + v3(0.15, 1.42, 0) + n * 0.1, 0.04, "steel")


def lever(bone, name, p, tilt=0.4):
    p = v3(*p)
    box(bone, name + "_base", p + v3(0, 0.08, 0), EYE, (0.2, 0.16, 0.3), "steel")
    beam(bone, "lit_%s_rod" % name, p + v3(0, 0.12, 0), p + v3(0, 0.75, math.sin(tilt) * 0.3), 0.04, "steel")
    box(bone, name + "_knob", p + v3(0, 0.78, math.sin(tilt) * 0.32), EYE, (0.08, 0.08, 0.08), "coral_red")


def speaking_tube(bone, name, p, top):
    p, top = v3(*p), v3(*top)
    beam(bone, "lit_" + name, p, top, 0.08, "brass")
    box(bone, name + "_mouth", p, EYE, (0.18, 0.18, 0.18), "brass")


# ---------------------------------------------------------------- projector, engine room
def projector(bone, name, lens_center, r=0.8, length=2.6):
    """Electric projector: a long brass barrel pointing forward (+z), the lens at its front, cooling rings,
    the carbon arc box behind, cables."""
    c = v3(*lens_center)
    for k in range(12):
        a0, a1 = 2 * math.pi * k / 12, 2 * math.pi * (k + 1) / 12
        p0 = v3(math.cos(a0) * r, math.sin(a0) * r, 0)
        p1 = v3(math.cos(a1) * r, math.sin(a1) * r, 0)
        mid = (p0 + p1) / 2
        add_cube(bone, "lit_%s_barrel%d" % (name, k), c + mid + v3(0, 0, -length / 2), gg.frame_from(v3(0, 0, 1), mid),
                 (length, 0.1, np.linalg.norm(p1 - p0) + 0.02), "brass")
    for z in (-0.3, -1.0, -1.7):
        for k in range(12):
            a0, a1 = 2 * math.pi * k / 12, 2 * math.pi * (k + 1) / 12
            beam(bone, "lit_%s_ring%d_%d" % (name, int(-z * 10), k), c + v3(math.cos(a0) * (r + 0.08), math.sin(a0) * (r + 0.08), z),
                 c + v3(math.cos(a1) * (r + 0.08), math.sin(a1) * (r + 0.08), z), 0.08, "steel")
    add_cube(bone, "glow_%s_lens" % name, c + v3(0, 0, -0.06), EYE, (1.45 * r, 1.45 * r, 0.04), "glow")
    box(bone, name + "_arc_box", c + v3(0, 0, -length - 0.35), EYE, (1.1, 1.1, 0.7), "steel")
    box(bone, name + "_yoke", c + v3(0, -r - 0.5, -length / 2), EYE, (0.3, 1.0, 0.3), "steel")
    beam(bone, "lit_%s_cable" % name, c + v3(0.4, -0.3, -length - 0.6), c + v3(0.8, -2.5, -length - 0.8), 0.07, "iron")


def battery_rack(bone, name, p, normal, cells=6, rows=2):
    """Rack of large battery cells (glass jars with copper plates and lit filaments), copper bus bars."""
    R, u, n = frame(normal)
    p = v3(*p)
    w = cells * 0.5
    for r_ in range(rows):
        y = 0.1 + r_ * 0.95
        box(bone, "%s_shelf%d" % (name, r_), p + v3(0, y, 0) + n * 0.35, R, (w + 0.2, 0.08, 0.7), "steel")
        for k in range(cells):
            q = p + u * (-w / 2 + 0.25 + k * 0.5) + v3(0, y + 0.38, 0) + n * 0.35
            add_cube(bone, "lit_%s_cell%d_%d" % (name, r_, k), q, R, (0.36, 0.66, 0.36), "battery", stretch=True)
            add_cube(bone, "glow_%s_filament%d_%d" % (name, r_, k), q + v3(0, 0.05, 0), R, (0.08, 0.3, 0.08), "glow")
            box(bone, "%s_cap%d_%d" % (name, r_, k), q + v3(0, 0.36, 0), R, (0.4, 0.06, 0.4), "copper")
        box(bone, "%s_bus%d" % (name, r_), p + v3(0, y + 0.8, 0) + n * 0.35, R, (w, 0.05, 0.08), "copper")
    for s in (-1, 1):
        box(bone, "%s_post%d" % (name, s > 0), p + u * s * (w / 2 + 0.1) + v3(0, 1.0, 0) + n * 0.35, R, (0.1, 2.0, 0.7), "steel")


def engine_block(bone, root, name, p, length=8.0, cylinders=4):
    """The great engine: a long steel bed, vertical cylinders with copper coils (electric motors and
    pistons), connecting rods and cranks driven by the shaft (bones "engine_piston_<k>" move with the
    "engine" animation), a flywheel (bone "engine_flywheel"), and the shaft (bone "engine_shaft")
    running aft to the propeller."""
    p = v3(*p)
    box(bone, name + "_bed", p + v3(0, 0.3, 0), EYE, (2.6, 0.6, length), "steel")
    pitch = length / (cylinders + 1)
    for k in range(cylinders):
        z = p[2] + length / 2 - pitch * (k + 1)
        base = v3(p[0], p[1], z)
        for s in (-1, 1):
            box(bone, "%s_coil%d%d" % (name, k, s > 0), base + v3(s * 0.85, 1.25, 0), EYE, (0.7, 1.3, 0.9), "coil")
            box(bone, "%s_coil_cap%d%d" % (name, k, s > 0), base + v3(s * 0.85, 1.95, 0), EYE, (0.76, 0.1, 0.96), "brass")
        box(bone, "%s_cyl%d" % (name, k), base + v3(0, 2.1, 0), EYE, (0.9, 1.6, 0.9), "steel")
        box(bone, "%s_cyl_top%d" % (name, k), base + v3(0, 2.95, 0), EYE, (1.0, 0.12, 1.0), "brass")
        piston = gg.Bone("engine_piston_%d" % k, origin=tuple(base + v3(0, 1.2, 0)), parent=root)
        box(piston, name + "_rod%d" % k, base + v3(0, 1.5, 0), EYE, (0.16, 1.2, 0.16), "brass")
        box(piston, name + "_crosshead%d" % k, base + v3(0, 1.05, 0), EYE, (0.4, 0.16, 0.3), "steel")
    shaft = gg.Bone("engine_shaft", origin=tuple(p + v3(0, 0.75, 0)), parent=root)
    box(shaft, name + "_shaft", p + v3(0, 0.75, -length / 2 - 4), EYE, (0.3, 0.3, length + 8), "brass")
    fly = gg.Bone("engine_flywheel", origin=tuple(p + v3(0, 0.75, length / 2 + 0.4)), parent=root)
    c = p + v3(0, 0.75, length / 2 + 0.4)
    for k in range(16):
        a0, a1 = 2 * math.pi * k / 16, 2 * math.pi * (k + 1) / 16
        beam(fly, "lit_%s_fly_rim%d" % (name, k), c + v3(math.cos(a0), math.sin(a0), 0) * 1.3, c + v3(math.cos(a1), math.sin(a1), 0) * 1.3,
             0.22, "steel", up=v3(0, 0, 1), width=0.3)
    for k in range(6):
        a = 2 * math.pi * k / 6
        beam(fly, "lit_%s_fly_spoke%d" % (name, k), c, c + v3(math.cos(a), math.sin(a), 0) * 1.25, 0.12, "steel")
    add_cube(fly, "lit_%s_fly_hub" % name, c, EYE, (0.4, 0.4, 0.4), "brass")


def pipe_run(bone, name, a, b, r=0.18, region="copper", flanges=True):
    a, b = v3(*a), v3(*b)
    beam(bone, "lit_" + name, a, b, 2 * r, region)
    if flanges:
        L = np.linalg.norm(b - a)
        n = max(1, int(L / 1.5))
        for k in range(n + 1):
            p = a + (b - a) * k / n
            beam(bone, "lit_%s_flange%d" % (name, k), p - norm(b - a) * 0.05, p + norm(b - a) * 0.05, 2 * r + 0.1, "brass")


def valve_wheel(bone, name, p, normal, r=0.22, region="coral_red"):
    R, u, n = frame(normal)
    p = v3(*p)
    for k in range(8):
        a0, a1 = 2 * math.pi * k / 8, 2 * math.pi * (k + 1) / 8
        beam(bone, "lit_%s_rim%d" % (name, k), p + (u * math.cos(a0) + v3(0, 1, 0) * math.sin(a0)) * r,
             p + (u * math.cos(a1) + v3(0, 1, 0) * math.sin(a1)) * r, 0.04, region, up=n)
    box(bone, name + "_hub", p, R, (0.08, 0.08, 0.1), "brass")
    box(bone, name + "_stem", p - n * 0.12, R, (0.06, 0.06, 0.2), "brass")


# ---------------------------------------------------------------- airlock, lifeboat
def diving_suit(bone, name, p, facing):
    """Diving suit on its stand: copper helmet with windows, canvas suit, lead boots, air tank."""
    R = ry(yaw_of(facing))
    p = v3(*p)
    box(bone, name + "_stand", p + v3(0, 0.05, 0), R, (0.7, 0.1, 0.6), "steel")
    for s in (-1, 1):
        box(bone, "%s_boot%d" % (name, s > 0), p + R @ v3(s * 0.15, 0.2, 0.05), R, (0.22, 0.3, 0.36), "iron")
        box(bone, "%s_leg%d" % (name, s > 0), p + R @ v3(s * 0.15, 0.75, 0), R, (0.24, 0.8, 0.26), "suit")
        box(bone, "%s_arm%d" % (name, s > 0), p + R @ v3(s * 0.38, 1.4, 0.02), R, (0.2, 0.7, 0.22), "suit")
        box(bone, "%s_glove%d" % (name, s > 0), p + R @ v3(s * 0.38, 1.0, 0.04), R, (0.18, 0.16, 0.2), "iron")
    box(bone, name + "_body", p + v3(0, 1.45, 0), R, (0.6, 0.8, 0.4), "suit")
    box(bone, name + "_collar", p + v3(0, 1.9, 0), R, (0.62, 0.12, 0.48), "copper")
    h = p + v3(0, 2.18, 0)
    box(bone, name + "_helmet", h, R, (0.5, 0.48, 0.5), "copper")
    box(bone, name + "_helmet_b", h, R @ gg.ry(math.pi / 4), (0.5, 0.42, 0.5), "copper")
    add_cube(bone, "lit_%s_window" % name, h + R @ v3(0, 0, 0.26), R, (0.26, 0.26, 0.04), {"all": "copper", "+3": "helmet"}, stretch=True)
    box(bone, name + "_tank", p + R @ v3(0, 1.45, -0.3), R, (0.3, 0.7, 0.2), "copper")
    beam(bone, "lit_%s_hose" % name, p + R @ v3(0.1, 1.85, -0.3), h + R @ v3(0.18, 0, -0.18), 0.05, "iron")


def tank(bone, name, p, h=1.6, r=0.35, region="copper"):
    p = v3(*p)
    box(bone, name, p + v3(0, h / 2, 0), EYE, (2 * r, h, 2 * r), region)
    box(bone, name + "_b", p + v3(0, h / 2, 0), gg.ry(math.pi / 4), (2 * r, h - 0.1, 2 * r), region)
    box(bone, name + "_top", p + v3(0, h + 0.05, 0), EYE, (2 * r * 0.6, 0.1, 2 * r * 0.6), "brass")


def lifeboat(bone, name, center, length=6.0, width=1.8):
    """Wooden lifeboat in its recess on the casing: planked hull, thwarts, oars."""
    c = v3(*center)
    n = 10
    for k in range(n):
        z0 = -length / 2 + length * k / n
        z1 = z0 + length / n
        zm = (z0 + z1) / 2
        f = 1 - (2 * zm / length) ** 2
        w = width / 2 * (0.25 + 0.75 * f ** 0.6)
        depth = 0.55 * (0.4 + 0.6 * f ** 0.5)
        for s in (-1, 1):
            box(bone, "%s_side%d%d" % (name, k, s > 0), c + v3(s * w, 0.05, zm), EYE, (0.1, 0.6, z1 - z0 + 0.02), "boat_wood")
        box(bone, "%s_bottom%d" % (name, k), c + v3(0, -depth + 0.3, zm), EYE, (2 * w, 0.1, z1 - z0 + 0.02), "boat_wood")
        box(bone, "%s_keel%d" % (name, k), c + v3(0, -depth + 0.2, zm), EYE, (0.12, 0.12, z1 - z0 + 0.02), "organ_wood")
    for k, z in enumerate((-1.5, 0.0, 1.5)):
        box(bone, "%s_thwart%d" % (name, k), c + v3(0, 0.15, z), EYE, (width * 0.85, 0.08, 0.3), "plank_light")
    for s in (-1, 1):
        beam(bone, "lit_%s_oar%d" % (name, s > 0), c + v3(s * 0.4, 0.25, -2.0), c + v3(s * 0.4, 0.25, 2.2), 0.08, "plank_light")
        beam(bone, "lit_%s_gunwale%d" % (name, s > 0), c + v3(s * width / 2 * 0.95, 0.36, -length / 2 + 0.3),
             c + v3(s * width / 2 * 0.95, 0.36, length / 2 - 0.3), 0.1, "organ_wood")


def railing(bone, name, points, h=1.0, posts_every=1.0):
    """Iron railing along a polyline (top rail, posts)."""
    pts = [v3(*p) for p in points]
    for k in range(len(pts) - 1):
        a, b = pts[k], pts[k + 1]
        beam(bone, "lit_%s_rail%d" % (name, k), a + v3(0, h, 0), b + v3(0, h, 0), 0.06, "steel")
        beam(bone, "lit_%s_mid%d" % (name, k), a + v3(0, h / 2, 0), b + v3(0, h / 2, 0), 0.04, "steel")
        L = np.linalg.norm(b - a)
        n = max(1, int(L / posts_every))
        for j in range(n + (1 if k == len(pts) - 2 else 0)):
            p = a + (b - a) * j / n
            box(bone, "%s_post%d_%d" % (name, k, j), p + v3(0, h / 2, 0), EYE, (0.06, h, 0.06), "steel")


def chart_sheet(bone, name, p, yaw=0.3):
    """Sea chart spread on a table."""
    p = v3(*p)
    add_cube(bone, "lit_" + name, p + v3(0, 0.008, 0), ry(yaw), (0.8, 0.012, 0.6), {"all": None, "+2": "chart"}, stretch=True)


def metal_chair(bone, name, p, facing):
    """Plain iron chair (Nemo's room)."""
    R = ry(yaw_of(facing))
    p = v3(*p)
    box(bone, name + "_seat", p + v3(0, 0.45, 0), R, (0.5, 0.06, 0.5), "steel")
    box(bone, name + "_back", p + R @ v3(0, 0.8, -0.23), R, (0.5, 0.6, 0.05), "steel")
    for sx in (-1, 1):
        for sz in (-1, 1):
            box(bone, "%s_leg%d%d" % (name, sx > 0, sz > 0), p + R @ v3(sx * 0.21, 0.22, sz * 0.21), R, (0.05, 0.44, 0.05), "steel")


def helm(bone, root, name, center):
    """The wheel of the wheelhouse on its pedestal; the wheel is the bone "helm_wheel" (turns with the helm)."""
    c = v3(*center)
    box(bone, name + "_pedestal", c - v3(0, 0.7, -0.25), EYE, (0.3, 1.0, 0.3), "organ_wood")
    box(bone, name + "_pedestal_cap", c - v3(0, 0.18, -0.25), EYE, (0.36, 0.1, 0.36), "brass")
    wheel = gg.Bone("helm_wheel", origin=tuple(c), parent=root)
    ship_wheel(wheel, name, c, (0, 0, 1), r=0.62)
