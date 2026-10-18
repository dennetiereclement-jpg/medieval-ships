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


def rx(a):
    return gg.rx(a)


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
    """Gilded electric chandelier: a chain, a turned boss over a bowl, one or two tiers of S-shaped arms
    ending in candle cups with lit flames, a ring hung with crystal drops."""
    hook = v3(*hook)
    c = hook - v3(0, drop, 0)
    for k in range(4):  # chain of links
        y = hook[1] - (k + 0.5) * drop * 0.6 / 4
        box(bone, "%s_link%d" % (name, k), v3(hook[0], y, hook[2]), ry(k * math.pi / 2), (0.08, drop * 0.6 / 4 + 0.02, 0.02), "gold")
    box(bone, name + "_canopy", hook - v3(0, 0.04, 0), ry(math.pi / 4), (0.3, 0.08, 0.3), "gold")
    box(bone, name + "_rod", c + v3(0, drop * 0.2, 0), EYE, (0.06, drop * 0.4, 0.06), "gold")
    for k, rot in enumerate((EYE, ry(math.pi / 4))):
        box(bone, "%s_boss%d" % (name, k), c, rot, (0.24, 0.3, 0.24), "gold")
        box(bone, "%s_bowl%d" % (name, k), c - v3(0, 0.26, 0), rot, (0.38, 0.14, 0.38), "gold")
    box(bone, name + "_finial", c - v3(0, 0.42, 0), ry(math.pi / 4), (0.1, 0.18, 0.1), "gold")
    for t in range(tiers):
        rr, y, k_n = r * (1 - 0.35 * t), -0.12 + 0.3 * t, n - 3 * t
        for k in range(k_n):
            a = 2 * math.pi * (k + 0.5 * t) / k_n
            d = v3(math.cos(a), 0, math.sin(a))
            p0 = c + v3(0, y - 0.1, 0) + d * 0.12
            p1 = c + v3(0, y - 0.18, 0) + d * (rr * 0.55)
            p2 = c + v3(0, y - 0.05, 0) + d * rr
            beam(bone, "lit_%s_arm%d_%d_a" % (name, t, k), p0, p1, 0.04, "gold")
            beam(bone, "lit_%s_arm%d_%d_b" % (name, t, k), p1, p2, 0.04, "gold")
            add_cube(bone, "lit_%s_cup%d_%d" % (name, t, k), p2 + v3(0, 0.02, 0), ry(math.pi / 4), (0.1, 0.05, 0.1), "gold")
            add_cube(bone, "lit_%s_candle%d_%d" % (name, t, k), p2 + v3(0, 0.1, 0), EYE, (0.05, 0.12, 0.05), "wax")
            add_cube(bone, "glow_%s_flame%d_%d" % (name, t, k), p2 + v3(0, 0.2, 0), ry(math.pi / 4), (0.05, 0.08, 0.05), "glow")
            if t == 0:
                drop_p = c + v3(0, y - 0.32, 0) + d * (rr * 0.62)
                add_cube(bone, "lit_%s_crystal%d" % (name, k), drop_p, ry(math.pi / 4), (0.05, 0.12, 0.05), "pearl")
        for k in range(k_n * 2):  # the ring the crystals hang from
            a0, a1 = 2 * math.pi * k / (k_n * 2), 2 * math.pi * (k + 1) / (k_n * 2)
            beam(bone, "lit_%s_ring%d_%d" % (name, t, k), c + v3(math.cos(a0) * rr * 0.62, y - 0.24, math.sin(a0) * rr * 0.62),
                 c + v3(math.cos(a1) * rr * 0.62, y - 0.24, math.sin(a1) * rr * 0.62), 0.025, "gold", extend=0.01)


def ceiling_lamp(bone, name, p):
    """Ceiling lamp of the working rooms: a brass rose, a short rod, a lit glass globe in a cage."""
    p = v3(*p)
    box(bone, name + "_rose", p - v3(0, 0.03, 0), ry(math.pi / 4), (0.3, 0.06, 0.3), "brass")
    box(bone, name + "_rod", p - v3(0, 0.15, 0), EYE, (0.05, 0.2, 0.05), "brass")
    g = p - v3(0, 0.38, 0)
    add_cube(bone, "glow_" + name, g, ry(math.pi / 4), (0.2, 0.24, 0.2), "glow")
    box(bone, name + "_cap", g + v3(0, 0.14, 0), ry(math.pi / 4), (0.24, 0.05, 0.24), "brass")
    box(bone, name + "_foot", g - v3(0, 0.14, 0), ry(math.pi / 4), (0.14, 0.04, 0.14), "brass")
    for k in range(4):
        a = math.pi / 2 * k
        box(bone, "%s_bar%d" % (name, k), g + v3(math.cos(a) * 0.13, 0, math.sin(a) * 0.13), EYE, (0.025, 0.28, 0.025), "brass")


def wall_lamp(bone, name, p, normal):
    """Brass sconce with a lit globe."""
    R, u, n = frame(normal)
    p = v3(*p)
    box(bone, name + "_plate", p + n * 0.02, R, (0.18, 0.28, 0.04), "brass")
    beam(bone, "lit_" + name + "_arm", p + n * 0.03, p + n * 0.22 + v3(0, 0.08, 0), 0.04, "brass")
    g = p + n * 0.24 + v3(0, 0.2, 0)
    add_cube(bone, "glow_" + name, g, EYE, (0.16, 0.2, 0.16), "glow")
    box(bone, name + "_cup", g - v3(0, 0.13, 0), EYE, (0.22, 0.06, 0.22), "brass")
    box(bone, name + "_cap", g + v3(0, 0.13, 0), EYE, (0.2, 0.05, 0.2), "brass")
    for k, (dx, dz) in enumerate(((1, 1), (1, -1), (-1, 1), (-1, -1))):
        box(bone, "%s_bar%d" % (name, k), g + v3(dx * 0.1, 0, dz * 0.1), EYE, (0.025, 0.24, 0.025), "brass")


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
def pipe(bone, name, foot, h, r, R, region="silver"):
    """An organ pipe: a round body (two crossed square prisms read as round), a conical foot, a dark
    mouth with its upper lip, a gilded band at the foot."""
    foot = v3(*foot)
    fh = min(0.45, h * 0.22)
    body = foot + v3(0, fh + (h - fh) / 2, 0)
    for k, rot in enumerate((R, R @ ry(math.pi / 4))):
        box(bone, "%s_body%d" % (name, k), body, rot, (r * 1.7, h - fh, r * 1.7), region)
    box(bone, name + "_foot", foot + v3(0, fh / 2, 0), R @ ry(math.pi / 4), (r * 1.1, fh, r * 1.1), region)
    n = R[:, 2]
    box(bone, name + "_mouth", foot + v3(0, fh + r * 1.1, 0) + n * (r * 0.86), R, (r * 1.0, r * 1.2, 0.02), "iron")
    box(bone, name + "_lip", foot + v3(0, fh + r * 1.85, 0) + n * (r * 0.87), R, (r * 1.1, r * 0.25, 0.02), "gold")
    box(bone, name + "_band", foot + v3(0, fh, 0), R @ ry(math.pi / 4), (r * 1.9, 0.05, r * 1.9), "gold")


def organ(bone, name, base, normal, width=5.2, height=5.2):
    """The monumental organ of the grand salon, against a wall (base = middle of its foot on the floor,
    `normal` towards the room): a carved case on panelled doors with gilded mouldings and pilasters,
    a round central tower of tall silver pipes, flats of pipes stepping down on each side under
    gilded arches, outer round towers with finials, a carved crest; the console with three keyboards,
    banks of stop knobs, a music desk, candles, a pedal board and a bench."""
    R, u, n = frame(normal)
    b = v3(*base)
    depth = 1.1
    W = width
    # ---- the case: plinth, panelled front with pilasters, cornice
    box(bone, name + "_plinth", b + v3(0, 0.12, 0) + n * (depth / 2 + 0.05), R, (W + 0.1, 0.24, depth + 0.1), "organ_wood")
    box(bone, name + "_case", b + v3(0, 1.15, 0) + n * (depth / 2), R, (W, 1.9, depth), "organ_wood")
    for k in range(6):
        x = -W / 2 + W * (k + 0.5) / 6
        if abs(x) < 1.2:
            continue  # the console stands there
        c = b + u * x + v3(0, 1.15, 0) + n * (depth + 0.01)
        for dy, hgt in ((0.0, 1.5),):
            box(bone, "%s_panel%d" % (name, k), c + v3(0, dy, 0), R, (W / 6 - 0.22, hgt, 0.03), "organ_wood")
            for sy in (-1, 1):
                box(bone, "%s_panel%d_mould_h%d" % (name, k, sy > 0), c + v3(0, sy * hgt / 2, 0) + n * 0.02, R, (W / 6 - 0.2, 0.04, 0.03), "gold")
            for sx in (-1, 1):
                box(bone, "%s_panel%d_mould_v%d" % (name, k, sx > 0), c + u * (sx * (W / 12 - 0.1)) + n * 0.02, R, (0.04, hgt, 0.03), "gold")
    for x in (-W / 2 + 0.05, -1.25, 1.25, W / 2 - 0.05):
        box(bone, "%s_pilaster_%d" % (name, int(x * 10)), b + u * x + v3(0, 1.15, 0) + n * (depth + 0.04), R, (0.18, 1.9, 0.08), "organ_wood")
        box(bone, "%s_pilaster_cap_%d" % (name, int(x * 10)), b + u * x + v3(0, 2.05, 0) + n * (depth + 0.06), R, (0.26, 0.1, 0.12), "gold")
    box(bone, name + "_cornice", b + v3(0, 2.2, 0) + n * (depth / 2 + 0.06), R, (W + 0.3, 0.2, depth + 0.22), "organ_wood")
    box(bone, name + "_cornice_gilt", b + v3(0, 2.32, 0) + n * (depth / 2 + 0.08), R, (W + 0.34, 0.05, depth + 0.26), "gold")
    box(bone, name + "_back", b + v3(0, height / 2, 0) + n * 0.12, R, (W, height, 0.24), "organ_wood")
    # ---- pipes
    yb = 2.35
    # round central tower: tall pipes on a half circle, a gilded cap and a crest above
    tower_r = 0.75
    for k in range(9):
        a = math.pi * k / 8
        off = u * (-math.cos(a) * tower_r) + n * (0.45 + math.sin(a) * 0.45)
        h = 2.45 - 0.35 * abs(k - 4) / 4
        pipe(bone, "%s_ctower%d" % (name, k), b + off + v3(0, yb, 0), h, 0.085, R)
    box(bone, name + "_ctower_cap", b + v3(0, yb + 2.55, 0) + n * 0.55, R, (1.8, 0.14, 1.1), "gold")
    for k in range(7):  # a carved fan (shell) crowning the centre
        a = math.pi * (k + 0.5) / 7
        beam(bone, "lit_%s_fan%d" % (name, k), b + v3(0, yb + 2.65, 0) + n * 0.5,
             b + u * (math.cos(a) * 0.8) + v3(0, yb + 2.65 + math.sin(a) * 0.65, 0) + n * 0.5, 0.06, "gold")
    # flats: pipes stepping down towards the sides, under a gilded arch
    for side in (-1, 1):
        x0, x1 = 1.0, W / 2 - 0.95
        count = 7
        for k in range(count):
            x = side * (x0 + (x1 - x0) * (k + 0.5) / count)
            h = 2.0 - 0.9 * (k / (count - 1)) ** 0.9
            pipe(bone, "%s_flat%d_%d" % (name, side > 0, k), b + u * x + v3(0, yb, 0) + n * 0.42, h, 0.07, R)
        for k in range(10):  # the arch over the flat
            t0, t1 = k / 10, (k + 1) / 10
            def arc(t):
                xx = side * (x0 + (x1 - x0) * t)
                return b + u * xx + v3(0, yb + 2.15 - 0.85 * t ** 1.4 + 0.25 * math.sin(math.pi * t), 0) + n * 0.5
            beam(bone, "lit_%s_arch%d_%d" % (name, side > 0, k), arc(t0), arc(t1), 0.08, "gold", width=0.06)
        # outer round tower with a finial
        tx = side * (W / 2 - 0.4)
        for k in range(5):
            a = math.pi * k / 4
            off = u * (tx - math.cos(a) * 0.3 * side) + n * (0.35 + math.sin(a) * 0.3)
            pipe(bone, "%s_otower%d_%d" % (name, side > 0, k), b + off + v3(0, yb, 0), 1.9 - 0.15 * abs(k - 2), 0.07, R)
        box(bone, "%s_otower_case%d" % (name, side > 0), b + u * tx + v3(0, yb - 0.1, 0) + n * 0.4, R, (0.9, 0.2, 0.8), "organ_wood")
        box(bone, "%s_otower_cap%d" % (name, side > 0), b + u * tx + v3(0, yb + 2.0, 0) + n * 0.4, R, (0.9, 0.12, 0.8), "gold")
        box(bone, "%s_finial%d" % (name, side > 0), b + u * tx + v3(0, yb + 2.2, 0) + n * 0.4, R @ ry(math.pi / 4), (0.18, 0.28, 0.18), "gold")
    # ---- console: three keyboards, stop knobs in terraces, music desk, candles, pedals, bench
    cz = depth + 0.38
    box(bone, name + "_console", b + v3(0, 0.55, 0) + n * cz, R, (2.3, 1.1, 0.76), "organ_wood")
    box(bone, name + "_console_top", b + v3(0, 1.12, 0) + n * cz, R, (2.4, 0.05, 0.8), "gold")
    for k, y in enumerate((0.93, 1.06, 1.19)):
        add_cube(bone, "lit_%s_keys%d" % (name, k), b + v3(0, y, 0) + n * (cz + 0.32 + 0.11 * (2 - k)), R, (1.7, 0.05, 0.22),
                 {"all": "organ_wood", "+2": "keys"}, stretch=True)
    for side in (-1, 1):
        box(bone, "%s_jamb%d" % (name, side > 0), b + u * (side * 1.02) + v3(0, 1.2, 0) + n * (cz + 0.12), R, (0.3, 0.55, 0.5), "organ_wood")
        for row in range(3):
            for col in range(2):
                p = b + u * (side * (0.92 + 0.14 * col)) + v3(0, 1.0 + 0.16 * row, 0) + n * (cz + 0.38)
                box(bone, "%s_stop%d_%d_%d" % (name, side > 0, row, col), p, R, (0.07, 0.07, 0.1), "wax")
                box(bone, "%s_stop_ring%d_%d_%d" % (name, side > 0, row, col), p - n * 0.04, R, (0.1, 0.1, 0.02), "gold")
        cand = b + u * (side * 1.05) + v3(0, 1.5, 0) + n * (cz + 0.1)
        box(bone, "%s_candle_holder%d" % (name, side > 0), cand, R, (0.12, 0.04, 0.12), "gold")
        box(bone, "%s_candle%d" % (name, side > 0), cand + v3(0, 0.14, 0), R, (0.05, 0.24, 0.05), "wax")
        add_cube(bone, "glow_%s_flame%d" % (name, side > 0), cand + v3(0, 0.3, 0), R, (0.04, 0.07, 0.04), "glow")
    desk = b + v3(0, 1.55, 0) + n * (cz + 0.05)
    box(bone, name + "_desk", desk, R @ rx(-0.25), (1.1, 0.5, 0.04), "organ_wood")
    box(bone, name + "_desk_rail", desk + v3(0, -0.24, 0) + n * 0.07, R, (1.1, 0.04, 0.06), "gold")
    box(bone, name + "_score", desk + n * 0.03, R @ rx(-0.25), (0.6, 0.4, 0.01), "chart")
    for k in range(9):  # pedal board
        x = -0.8 + 1.6 * k / 8
        box(bone, "%s_pedal%d" % (name, k), b + u * x + v3(0, 0.07, 0) + n * (cz + 0.7), R, (0.1, 0.06, 0.6), "organ_wood" if k % 2 else "wax")
    bench = b + n * (cz + 1.1)
    box(bone, name + "_bench", bench + v3(0, 0.48, 0), R, (1.5, 0.1, 0.42), "organ_wood")
    box(bone, name + "_bench_cushion", bench + v3(0, 0.55, 0), R, (1.4, 0.06, 0.36), "red_velvet")
    for s in (-1, 1):
        box(bone, "%s_bench_leg%d" % (name, s > 0), bench + u * s * 0.62 + v3(0, 0.22, 0), R, (0.1, 0.44, 0.36), "organ_wood")
        box(bone, "%s_bench_foot%d" % (name, s > 0), bench + u * s * 0.62 + v3(0, 0.03, 0), R, (0.16, 0.06, 0.44), "gold")


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


def clam_basin(bone, name, p, r=0.8):
    """The giant tridacna of the salon (Verne: a basin made of one shell, a fountain of sea water
    running into it): a turned gilded pedestal, the two scalloped valves of the shell opened wide with
    their ribs, the water inside, a jet with its spray."""
    p = v3(*p)
    for k, rot in enumerate((EYE, ry(math.pi / 4))):
        box(bone, "%s_foot%d" % (name, k), p + v3(0, 0.06, 0), rot, (r * 1.1, 0.12, r * 1.1), "organ_wood")
        box(bone, "%s_knop%d" % (name, k), p + v3(0, 0.3, 0), rot, (0.34, 0.36, 0.34), "gold")
        box(bone, "%s_cup%d" % (name, k), p + v3(0, 0.58, 0), rot, (0.5, 0.2, 0.5), "organ_wood")
    c = p + v3(0, 0.78, 0)
    n = 11
    for side in (-1, 1):  # the two valves, each a fan of ribs rising from the hinge
        for k in range(n):
            a = math.pi * (k + 0.5) / n
            d = norm(v3(math.cos(a), 0, side * math.sin(a)))
            tip = c + d * r + v3(0, 0.22 + 0.06 * math.sin(a * 3), 0)
            reg = "shell" if k % 2 else "pearl"
            beam(bone, "lit_%s_rib%d_%d" % (name, side > 0, k), c + d * 0.12 - v3(0, 0.04, 0), tip, 0.17, reg)
            box(bone, "%s_scallop%d_%d" % (name, side > 0, k), tip + v3(0, 0.03, 0), ry(-math.atan2(d[2], d[0])), (0.12, 0.06, 0.2), "shell")
    for k, rot in enumerate((EYE, ry(math.pi / 4))):
        box(bone, "%s_water%d" % (name, k), c + v3(0, 0.12, 0), rot, (r * 1.25, 0.04, r * 1.25), "glass")
    # the fountain: a gilded dolphin spout in the middle, a short jet falling back in a ring of drops
    box(bone, name + "_spout", c + v3(0, 0.24, 0), ry(math.pi / 4), (0.14, 0.24, 0.14), "gold")
    box(bone, name + "_jet", c + v3(0, 0.5, 0), EYE, (0.05, 0.3, 0.05), "glass")
    for k in range(6):
        a = 2 * math.pi * k / 6
        box(bone, "%s_drop%d" % (name, k), c + v3(math.cos(a) * 0.18, 0.55, math.sin(a) * 0.18), EYE, (0.05, 0.05, 0.05), "glass")
    box(bone, name + "_pearl", c + v3(0.2, 0.17, 0.1), EYE, (0.12, 0.12, 0.12), "pearl")


def telescope(bone, name, p, facing):
    """A brass telescope on a wooden tripod, aimed at the window."""
    R = ry(yaw_of(facing))
    p = v3(*p)
    head = p + v3(0, 1.15, 0)
    for k in range(3):
        a = 2 * math.pi * k / 3 + 0.4
        beam(bone, "lit_%s_leg%d" % (name, k), p + v3(math.cos(a) * 0.4, 0.0, math.sin(a) * 0.4), head, 0.05, "organ_wood")
    box(bone, name + "_mount", head, EYE, (0.14, 0.12, 0.14), "brass")
    d = R @ norm(v3(0, 0.25, 1))
    beam(bone, "lit_%s_tube" % name, head - d * 0.55, head + d * 0.5, 0.13, "brass")
    beam(bone, "lit_%s_hood" % name, head + d * 0.42, head + d * 0.62, 0.17, "brass")
    beam(bone, "lit_%s_eyepiece" % name, head - d * 0.7, head - d * 0.5, 0.07, "iron")
    beam(bone, "lit_%s_band" % name, head - d * 0.05, head + d * 0.05, 0.155, "gold")


def potted_palm(bone, name, p, h=2.2):
    """A palm in a brass-banded jardinière: the pot, a ringed trunk leaning a little, a crown of
    arching fronds."""
    p = v3(*p)
    for k, rot in enumerate((EYE, ry(math.pi / 4))):
        box(bone, "%s_pot%d" % (name, k), p + v3(0, 0.3, 0), rot, (0.56, 0.6, 0.56), "organ_wood")
        box(bone, "%s_band%d" % (name, k), p + v3(0, 0.52, 0), rot, (0.6, 0.06, 0.6), "brass")
        box(bone, "%s_rim%d" % (name, k), p + v3(0, 0.62, 0), rot, (0.62, 0.05, 0.62), "gold")
    top = p + v3(0.08, h, 0.05)
    beam(bone, "lit_%s_trunk" % name, p + v3(0, 0.6, 0), top, 0.12, "organ_wood")
    for k in range(4):
        y = 0.9 + k * (h - 0.9) / 4
        box(bone, "%s_ring%d" % (name, k), p + v3(0.08 * y / h, y, 0.05 * y / h), ry(0.4 * k), (0.16, 0.04, 0.16), "boat_wood")
    for k in range(8):
        a = 2 * math.pi * k / 8 + 0.2
        d = v3(math.cos(a), 0, math.sin(a))
        mid = top + d * 0.45 + v3(0, 0.18, 0)
        tip = top + d * 0.95 - v3(0, 0.25, 0)
        beam(bone, "lit_%s_frond%d_a" % (name, k), top, mid, 0.16, "green_leather")
        beam(bone, "lit_%s_frond%d_b" % (name, k), mid, tip, 0.12, "green_leather")


def pilaster(bone, name, p, normal, h):
    """A fluted pilaster against a wall, gilded base and Corinthian-like capital."""
    R, u, n = frame(normal)
    p = v3(*p)
    box(bone, name + "_shaft", p + v3(0, h / 2, 0) + n * 0.08, R, (0.34, h, 0.16), "organ_wood")
    for k in (-1, 0, 1):
        box(bone, "%s_flute%d" % (name, k), p + v3(0, h / 2, 0) + u * (k * 0.09) + n * 0.165, R, (0.025, h - 0.7, 0.01), "gold")
    box(bone, name + "_base", p + v3(0, 0.15, 0) + n * 0.11, R, (0.44, 0.3, 0.22), "gold")
    box(bone, name + "_capital", p + v3(0, h - 0.22, 0) + n * 0.12, R, (0.46, 0.24, 0.24), "gold")
    box(bone, name + "_abacus", p + v3(0, h - 0.05, 0) + n * 0.14, R, (0.54, 0.1, 0.28), "gold")


def cornice(bone, name, x0, x1, z0, z1, y):
    """A gilded cornice round a room under its ceiling (y = ceiling), with a band of dentils."""
    for k, (a, b) in enumerate(((v3(x0, 0, z0), v3(x1, 0, z0)), (v3(x0, 0, z1), v3(x1, 0, z1)),
                                (v3(x0, 0, z0), v3(x0, 0, z1)), (v3(x1, 0, z0), v3(x1, 0, z1)))):
        along = norm(b - a)
        inward = v3(-along[2], 0, along[0])
        mid = (a + b) / 2
        if np.dot(inward, v3((x0 + x1) / 2, 0, (z0 + z1) / 2) - mid) < 0:
            inward = -inward
        R = np.column_stack([np.cross(v3(0, 1, 0), inward), v3(0, 1, 0), inward])
        length = float(np.linalg.norm(b - a))
        box(bone, "%s_%d_top" % (name, k), mid + v3(0, y - 0.1, 0) + inward * 0.12, R, (length, 0.2, 0.24), "gold")
        box(bone, "%s_%d_band" % (name, k), mid + v3(0, y - 0.32, 0) + inward * 0.05, R, (length, 0.24, 0.1), "organ_wood")
        for j in range(int(length / 0.3)):
            t = -length / 2 + 0.15 + j * 0.3
            box(bone, "%s_%d_dentil%d" % (name, k, j), mid + v3(0, y - 0.27, 0) + inward * 0.12 + R[:, 0] * t, R, (0.12, 0.12, 0.06), "gold")


def ceiling_rose(bone, name, p, r=0.7):
    """A gilded rose on the ceiling round the hook of a chandelier."""
    p = v3(*p)
    for k in range(3):
        box(bone, "%s_%d" % (name, k), p - v3(0, 0.03 + 0.03 * k, 0), ry(math.pi / 6 * k), (r * (1 - 0.25 * k) * 2, 0.05, r * (1 - 0.25 * k) * 2),
            "gold" if k != 1 else "organ_wood")


def armchair(bone, name, p, facing, region="red_velvet"):
    """Wing armchair in velvet: a plump seat cushion, a curved buttoned back, rolled arms with gilded
    fronts, wings, a carved apron and cabriole legs; the sitter looks along `facing`."""
    R = ry(yaw_of(facing))
    p = v3(*p)
    P = lambda x, y, z: p + R @ v3(x, y, z)
    box(bone, name + "_frame", P(0, 0.3, 0.0), R, (0.84, 0.16, 0.8), region)
    box(bone, name + "_apron", P(0, 0.24, 0.41), R, (0.78, 0.1, 0.03), "gold")
    box(bone, name + "_cushion", P(0, 0.44, 0.04), R, (0.66, 0.14, 0.7), region)
    box(bone, name + "_cushion_top", P(0, 0.52, 0.04), R, (0.6, 0.04, 0.64), region)
    # back in three tilted pieces (curved), buttons
    for k, (y, z, tilt) in enumerate(((0.72, -0.33, 0.1), (1.0, -0.37, 0.05), (1.26, -0.38, -0.08))):
        box(bone, "%s_back%d" % (name, k), P(0, y, z), R @ rx(tilt), (0.8 - 0.06 * k, 0.3, 0.16), region)
    box(bone, name + "_crest", P(0, 1.43, -0.37), R, (0.6, 0.08, 0.14), region)
    for k in range(4):
        box(bone, "%s_button%d" % (name, k), P(-0.18 + 0.12 * k, 0.95 + 0.12 * (k % 2), -0.28), R, (0.03, 0.03, 0.02), "gold")
    for s_ in (-1, 1):
        box(bone, "%s_arm%d" % (name, s_ > 0), P(s_ * 0.37, 0.56, 0.02), R, (0.12, 0.34, 0.76), region)
        box(bone, "%s_roll%d" % (name, s_ > 0), P(s_ * 0.39, 0.75, 0.02), R, (0.18, 0.1, 0.8), region)
        box(bone, "%s_arm_front%d" % (name, s_ > 0), P(s_ * 0.39, 0.62, 0.42), R, (0.16, 0.26, 0.03), "gold")
        box(bone, "%s_wing%d" % (name, s_ > 0), P(s_ * 0.38, 1.08, -0.24), R @ ry(s_ * 0.2), (0.1, 0.56, 0.3), region)
        for t in (-1, 1):
            # cabriole leg: knee out, ankle in, a gilded foot
            box(bone, "%s_knee%d%d" % (name, s_ > 0, t > 0), P(s_ * 0.35, 0.18, t * 0.33), R @ rx(t * 0.25), (0.07, 0.14, 0.07), "organ_wood")
            box(bone, "%s_foot%d%d" % (name, s_ > 0, t > 0), P(s_ * 0.36, 0.05, t * 0.36), R, (0.08, 0.08, 0.08), "gold")


def chesterfield(bone, name, p, facing, length=2.4, region="green_leather"):
    """Chesterfield sofa in leather: deep-buttoned back and arms of the same height, scrolled arm
    fronts, two seat cushions, turned feet; the sitters look along `facing`."""
    R = ry(yaw_of(facing))
    p = v3(*p)
    P = lambda x, y, z: p + R @ v3(x, y, z)
    box(bone, name + "_base", P(0, 0.24, 0), R, (length, 0.26, 0.92), region)
    for k in (-1, 1):
        box(bone, "%s_cushion%d" % (name, k > 0), P(k * (length - 0.55) / 4, 0.44, 0.06), R, ((length - 0.6) / 2 - 0.03, 0.15, 0.74), region)
    box(bone, name + "_back", P(0, 0.72, -0.36), R @ rx(0.06), (length - 0.1, 0.58, 0.22), region)
    for s_ in (-1, 1):
        box(bone, "%s_arm%d" % (name, s_ > 0), P(s_ * (length / 2 - 0.14), 0.56, 0.0), R, (0.26, 0.42, 0.92), region)
        box(bone, "%s_roll%d" % (name, s_ > 0), P(s_ * (length / 2 - 0.1), 0.78, 0.0), R, (0.36, 0.14, 0.96), region)
        box(bone, "%s_scroll%d" % (name, s_ > 0), P(s_ * (length / 2 - 0.1), 0.66, 0.48), R, (0.3, 0.3, 0.03), region)
        for t in (-1, 1):
            box(bone, "%s_foot%d%d" % (name, s_ > 0, t > 0), P(s_ * (length / 2 - 0.15), 0.05, t * 0.36), R @ ry(math.pi / 4),
                (0.1, 0.1, 0.1), "organ_wood")
    # deep buttoning: rows of buttons on the back and the arms
    for row in range(2):
        for k in range(int(length / 0.3)):
            x = -length / 2 + 0.3 + k * 0.3 + (0.15 if row else 0)
            if abs(x) < length / 2 - 0.3:
                box(bone, "%s_btn%d_%d" % (name, row, k), P(x, 0.68 + 0.18 * row, -0.24), R, (0.03, 0.03, 0.02), "gold")


def globe(bone, name, p):
    """Terrestrial globe: a round ball (bands of panels mapped with a world map) tilted on its axis,
    a brass meridian ring, a gilded horizon ring, a turned stand on three legs."""
    p = v3(*p)
    for k in range(3):
        a = 2 * math.pi * k / 3
        beam(bone, "lit_%s_leg%d" % (name, k), p + v3(math.cos(a) * 0.3, 0.0, math.sin(a) * 0.3), p + v3(0, 0.55, 0), 0.06, "organ_wood")
    box(bone, name + "_knop", p + v3(0, 0.6, 0), EYE, (0.14, 0.14, 0.14), "gold")
    box(bone, name + "_column", p + v3(0, 0.72, 0), EYE, (0.08, 0.22, 0.08), "organ_wood")
    c = p + v3(0, 1.12, 0)
    r = 0.34
    tilt = gg.rx(0.41)
    nlat, nlon = 8, 16
    def P(i, j):
        lat = -math.pi / 2 + math.pi * i / nlat
        lon = 2 * math.pi * j / nlon
        return c + tilt @ v3(math.cos(lat) * math.cos(lon) * r, math.sin(lat) * r, math.cos(lat) * math.sin(lon) * r)
    for i in range(nlat):
        for j in range(nlon):
            a0, a1, b0, b1 = P(i, j), P(i, j + 1), P(i + 1, j), P(i + 1, j + 1)
            if np.linalg.norm(a1 - a0) < 1e-3 and np.linalg.norm(b1 - b0) < 1e-3:
                continue
            mid = (a0 + a1 + b0 + b1) / 4
            cube = gg.board(bone, "lit_%s_ball%d_%d" % (name, i, j), a0, a1, b0, b1, 0.02, "globe", mid - c, overlap=1.04)
            for f in cube.faces.values():
                if f is not None:
                    f["stretch"] = True
                    f["sub"] = (j / nlon, 1 - (i + 1) / nlat, (j + 1) / nlon, 1 - i / nlat)
    for k in range(16):  # meridian, round the tilted axis
        a0, a1 = 2 * math.pi * k / 16, 2 * math.pi * (k + 1) / 16
        q0 = c + tilt @ v3(0, math.cos(a0) * (r + 0.05), math.sin(a0) * (r + 0.05))
        q1 = c + tilt @ v3(0, math.cos(a1) * (r + 0.05), math.sin(a1) * (r + 0.05))
        beam(bone, "lit_%s_meridian%d" % (name, k), q0, q1, 0.035, "brass")
        h0 = c + v3(math.cos(a0) * (r + 0.1), 0, math.sin(a0) * (r + 0.1))
        h1 = c + v3(math.cos(a1) * (r + 0.1), 0, math.sin(a1) * (r + 0.1))
        beam(bone, "lit_%s_horizon%d" % (name, k), h0, h1, 0.05, "gold", width=0.06)
    for s_ in (-1, 1):
        beam(bone, "lit_%s_horizon_post%d" % (name, s_ > 0), p + v3(0, 0.62, 0), c + v3(s_ * (r + 0.1), 0, 0), 0.04, "organ_wood")


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
    axis_y = 1.55  # the crankshaft, high enough for the wheels to clear the floor
    shaft = gg.Bone("engine_shaft", origin=tuple(p + v3(0, axis_y, 0)), parent=root)
    box(shaft, name + "_shaft", p + v3(0, axis_y, -length / 2 - 4), EYE, (0.3, 0.3, length + 8), "brass")
    for k in range(cylinders):
        z = p[2] + length / 2 - pitch * (k + 1)
        box(shaft, "%s_crank%d" % (name, k), p + v3(0, axis_y + 0.25, z - p[2]), EYE, (0.18, 0.55, 0.22), "steel")
    fly = gg.Bone("engine_flywheel", origin=tuple(p + v3(0, axis_y, length / 2 + 0.35)), parent=root)
    c = p + v3(0, axis_y, length / 2 + 0.35)
    for k in range(16):
        a0, a1 = 2 * math.pi * k / 16, 2 * math.pi * (k + 1) / 16
        beam(fly, "lit_%s_fly_rim%d" % (name, k), c + v3(math.cos(a0), math.sin(a0), 0) * 1.3, c + v3(math.cos(a1), math.sin(a1), 0) * 1.3,
             0.22, "steel", up=v3(0, 0, 1), width=0.3)
    for k in range(6):
        a = 2 * math.pi * k / 6
        beam(fly, "lit_%s_fly_spoke%d" % (name, k), c, c + v3(math.cos(a), math.sin(a), 0) * 1.25, 0.12, "steel")
    add_cube(fly, "lit_%s_fly_hub" % name, c, EYE, (0.4, 0.4, 0.4), "brass")
    # two great toothed wheels on the catwalk side, driven by the shaft (bones "engine_gear_<k>")
    for g_i, dz in enumerate((-length * 0.2, length * 0.2)):
        gc = p + v3(1.45, axis_y, dz)
        gear = gg.Bone("engine_gear_%d" % g_i, origin=tuple(gc), parent=root)
        r = 1.15
        for k in range(20):
            a0, a1 = 2 * math.pi * k / 20, 2 * math.pi * (k + 1) / 20
            q0 = gc + v3(0, math.sin(a0), math.cos(a0)) * r
            q1 = gc + v3(0, math.sin(a1), math.cos(a1)) * r
            beam(gear, "lit_%s_gear%d_rim%d" % (name, g_i, k), q0, q1, 0.2, "brass" if g_i else "copper", up=v3(1, 0, 0), width=0.18)
            am = (a0 + a1) / 2
            tooth = gc + v3(0, math.sin(am), math.cos(am)) * (r + 0.14)
            box(gear, "%s_gear%d_tooth%d" % (name, g_i, k), tooth, EYE, (0.16, 0.16, 0.16), "brass" if g_i else "copper")
        for k in range(5):
            a = 2 * math.pi * k / 5
            beam(gear, "lit_%s_gear%d_spoke%d" % (name, g_i, k), gc, gc + v3(0, math.sin(a), math.cos(a)) * (r - 0.05), 0.14, "steel")
        add_cube(gear, "lit_%s_gear%d_hub" % (name, g_i), gc, EYE, (0.3, 0.36, 0.36), "brass")
        box(bone, "%s_gear%d_bearing" % (name, g_i), gc + v3(0, -(axis_y - 0.3) / 2 - 0.15, 0), EYE, (0.3, axis_y - 0.3, 0.4), "steel")


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
    """Diving suit on its stand (panel 14): a round copper helmet with three barred windows on a bolted
    breastplate, the canvas suit, a belt of lead weights, gloves, heavy boots, the air tank and hose."""
    R = ry(yaw_of(facing))
    p = v3(*p)
    box(bone, name + "_stand", p + v3(0, 0.05, 0), R, (0.72, 0.1, 0.62), "steel")
    for s_ in (-1, 1):
        box(bone, "%s_boot%d" % (name, s_ > 0), p + R @ v3(s_ * 0.15, 0.22, 0.04), R, (0.24, 0.26, 0.38), "iron")
        box(bone, "%s_sole%d" % (name, s_ > 0), p + R @ v3(s_ * 0.15, 0.11, 0.05), R, (0.27, 0.06, 0.42), "copper")
        for k, rot in enumerate((R, R @ ry(math.pi / 4))):
            box(bone, "%s_leg%d_%d" % (name, s_ > 0, k), p + R @ v3(s_ * 0.15, 0.76, 0), rot, (0.24, 0.82, 0.24), "suit")
            box(bone, "%s_arm%d_%d" % (name, s_ > 0, k), p + R @ v3(s_ * 0.39, 1.38, 0.02), rot @ gg.rz(s_ * 0.12), (0.2, 0.66, 0.2), "suit")
        box(bone, "%s_cuff%d" % (name, s_ > 0), p + R @ v3(s_ * 0.42, 1.06, 0.03), R, (0.2, 0.06, 0.2), "copper")
        box(bone, "%s_glove%d" % (name, s_ > 0), p + R @ v3(s_ * 0.43, 0.94, 0.04), R, (0.17, 0.18, 0.2), "iron")
    for k, rot in enumerate((R, R @ ry(math.pi / 4))):
        box(bone, "%s_body%d" % (name, k), p + v3(0, 1.42, 0), rot, (0.56, 0.78, 0.4), "suit")
    box(bone, name + "_belt", p + v3(0, 1.08, 0), R, (0.62, 0.1, 0.46), "iron")
    for k in range(3):
        box(bone, "%s_weight%d" % (name, k), p + R @ v3(-0.18 + 0.18 * k, 1.0, 0.24), R, (0.12, 0.14, 0.06), "steel")
    # breastplate: copper, bolted
    box(bone, name + "_corselet", p + v3(0, 1.86, 0), R, (0.7, 0.16, 0.56), "copper")
    box(bone, name + "_corselet_low", p + R @ v3(0, 1.72, 0.12), R, (0.6, 0.14, 0.34), "copper")
    for k in range(8):
        a = 2 * math.pi * k / 8
        box(bone, "%s_bolt%d" % (name, k), p + R @ v3(math.cos(a) * 0.32, 1.95, math.sin(a) * 0.26), R, (0.05, 0.05, 0.05), "brass")
    # the helmet: round (three crossed boxes), front window and two side windows with bars
    h = p + v3(0, 2.2, 0)
    for k in range(3):
        box(bone, "%s_helmet%d" % (name, k), h, R @ ry(k * math.pi / 6), (0.5, 0.5, 0.5), "copper")
    box(bone, name + "_helmet_top", h + v3(0, 0.27, 0), R @ ry(math.pi / 4), (0.32, 0.08, 0.32), "copper")
    for k, (d, side) in enumerate(((v3(0, 0, 1), 0), (v3(1, 0, 0), 1), (v3(-1, 0, 0), -1))):
        n = R @ d
        size = 0.26 if k == 0 else 0.18
        rot = R if k == 0 else R @ ry(math.pi / 2)
        add_cube(bone, "lit_%s_window%d" % (name, k), h + n * 0.28, rot, (size, size, 0.04), {"all": "brass", "+3": "helmet", "-3": "helmet"},
                 stretch=True)
        for q in range(8):
            a0, a1 = 2 * math.pi * q / 8, 2 * math.pi * (q + 1) / 8
            ax, ay = rot[:, 0], rot[:, 1]
            beam(bone, "lit_%s_rim%d_%d" % (name, k, q), h + n * 0.3 + (ax * math.cos(a0) + ay * math.sin(a0)) * size * 0.62,
                 h + n * 0.3 + (ax * math.cos(a1) + ay * math.sin(a1)) * size * 0.62, 0.04, "brass", up=n)
    # air tank and hose
    for k, rot in enumerate((R, R @ ry(math.pi / 4))):
        box(bone, "%s_tank%d" % (name, k), p + R @ v3(0, 1.45, -0.32), rot, (0.28, 0.74, 0.28), "copper")
    box(bone, name + "_tank_valve", p + R @ v3(0, 1.88, -0.32), R, (0.1, 0.12, 0.1), "brass")
    beam(bone, "lit_%s_hose_a" % name, p + R @ v3(0, 1.92, -0.32), p + R @ v3(0.2, 2.05, -0.26), 0.05, "iron")
    beam(bone, "lit_%s_hose_b" % name, p + R @ v3(0.2, 2.05, -0.26), h + R @ v3(0.2, 0, -0.18), 0.05, "iron")


def tank(bone, name, p, h=1.6, r=0.35, region="copper"):
    p = v3(*p)
    box(bone, name, p + v3(0, h / 2, 0), EYE, (2 * r, h, 2 * r), region)
    box(bone, name + "_b", p + v3(0, h / 2, 0), gg.ry(math.pi / 4), (2 * r, h - 0.1, 2 * r), region)
    box(bone, name + "_top", p + v3(0, h + 0.05, 0), EYE, (2 * r * 0.6, 0.1, 2 * r * 0.6), "brass")


def lifeboat(bone, name, center, length=6.0, width=1.8):
    """Wooden lifeboat in its recess on the casing (panel 15): a rounded planked hull (lofted strakes
    following a curved sheer and a round bilge), a keel, stem and stern posts, a varnished gunwale
    following the sheer, thwarts, oars and a coiled painter."""
    c = v3(*center)
    nz, ns_ = 14, 5
    def P(t, a):
        # t: -1 (stern) .. 1 (bow); a: 0 (keel) .. 1 (gunwale), one side
        f = 1 - abs(t) ** 2.2
        half = width / 2 * (0.18 + 0.82 * f ** 0.55)
        depth = 0.62 * (0.35 + 0.65 * f ** 0.4)
        sheer = 0.38 + 0.18 * abs(t) ** 3
        x = half * math.sin(a * math.pi / 2)
        y = sheer - depth + (depth + 0.0) * (1 - math.cos(a * math.pi / 2)) * 1.0
        return x, y, t * length / 2
    for side in (-1, 1):
        sections = []
        for i in range(nz + 1):
            t = -1 + 2 * i / nz
            sec = []
            for j in range(ns_ + 1):
                x, y, z = P(t, j / ns_)
                sec.append(c + v3(side * x, y, z))
            sections.append(sec)
        for i in range(nz):
            for j in range(ns_):
                a0, a1, b0, b1 = sections[i][j], sections[i][j + 1], sections[i + 1][j], sections[i + 1][j + 1]
                mid = (a0 + a1 + b0 + b1) / 4
                out = mid - (c + v3(0, 0.6, mid[2] - c[2]))
                gg.board(bone, "lit_%s_strake%d_%d_%d" % (name, side > 0, i, j), a0, a1, b0, b1, 0.05,
                         "boat_wood" if j < ns_ - 1 else "organ_wood", out, overlap=1.04)
        for i in range(nz):  # gunwale along the sheer
            x0, y0, z0 = P(-1 + 2 * i / nz, 1.0)
            x1, y1, z1 = P(-1 + 2 * (i + 1) / nz, 1.0)
            beam(bone, "lit_%s_gunwale%d_%d" % (name, side > 0, i), c + v3(side * x0, y0 + 0.03, z0), c + v3(side * x1, y1 + 0.03, z1),
                 0.08, "organ_wood", width=0.1)
    for i in range(nz):
        _, y0, z0 = P(-1 + 2 * i / nz, 0.0)
        _, y1, z1 = P(-1 + 2 * (i + 1) / nz, 0.0)
        beam(bone, "lit_%s_keel%d" % (name, i), c + v3(0, y0 - 0.04, z0), c + v3(0, y1 - 0.04, z1), 0.1, "organ_wood")
    for t, tag in ((1.0, "stem"), (-1.0, "sternpost")):
        x, y, z = P(t, 0.0)
        beam(bone, "lit_%s_%s" % (name, tag), c + v3(0, y, z), c + v3(0, 0.62, z + 0.08 * t), 0.1, "organ_wood")
    for k, t in enumerate((-0.55, 0.0, 0.5)):
        x, y, z = P(t, 1.0)
        box(bone, "%s_thwart%d" % (name, k), c + v3(0, y - 0.18, z), EYE, (2 * x * 0.92, 0.06, 0.32), "plank_light")
    for s_ in (-1, 1):
        beam(bone, "lit_%s_oar%d" % (name, s_ > 0), c + v3(s_ * 0.35, 0.12, -2.1), c + v3(s_ * 0.35, 0.14, 2.0), 0.07, "plank_light")
        box(bone, "%s_blade%d" % (name, s_ > 0), c + v3(s_ * 0.35, 0.14, 2.2), EYE, (0.18, 0.03, 0.5), "plank_light")
    for k in range(8):  # coiled painter at the bow
        a0, a1 = 2 * math.pi * k / 8, 2 * math.pi * (k + 1) / 8
        q = c + v3(0, 0.12, length / 2 - 0.9)
        beam(bone, "lit_%s_rope%d" % (name, k), q + v3(math.cos(a0) * 0.18, 0, math.sin(a0) * 0.18),
             q + v3(math.cos(a1) * 0.18, 0, math.sin(a1) * 0.18), 0.05, "plank_light")


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
