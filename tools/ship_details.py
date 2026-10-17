"""Small deck details shared by the ship model generators (barrels, crates, coiled ropes,
fife rails with belaying pins, bells, amphorae...).

Every function takes the generator module `m` (for its add_cube / beam helpers and its uuid
counter) and region names, since each ship has its own texture atlas. All details are
decorative: they have no collision.
"""
import math

import numpy as np

EYE = np.eye(3)


def v3(*a):
    return np.array(a, dtype=float)


def ry(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def barrel(m, bone, name, p, h=0.75, r=0.27, wood="hull_mid", ends="end_grain", hoop="iron"):
    """Upright barrel with a slight bulge and two iron hoops."""
    p = v3(*p)
    m.add_cube(bone, name, p + v3(0, h / 2, 0), EYE, (2 * r, h, 2 * r), {"all": wood, "+2": ends, "-2": ends})
    m.add_cube(bone, name + "_bulge", p + v3(0, h / 2, 0), EYE, (2 * r + 0.07, h * 0.42, 2 * r + 0.07),
               {"all": wood, "+2": None, "-2": None})
    for k, f in enumerate((0.16, 0.84)):
        m.add_cube(bone, "%s_hoop%d" % (name, k), p + v3(0, h * f, 0), EYE, (2 * r + 0.05, 0.06, 2 * r + 0.05),
                   {"all": hoop, "+2": None, "-2": None})


def lying_barrel(m, bone, name, p, yaw=0.0, h=0.75, r=0.27, wood="hull_mid", ends="end_grain", hoop="iron"):
    """Barrel lying on its side (rolled along the deck)."""
    p = v3(*p)
    R = ry(yaw) @ np.array([[0, 1, 0], [-1, 0, 0], [0, 0, 1]], dtype=float)
    m.add_cube(bone, name, p + v3(0, r, 0), R, (2 * r, h, 2 * r), {"all": wood, "+2": ends, "-2": ends})
    for k, f in enumerate((-0.33, 0.33)):
        off = R @ v3(0, h * f, 0)
        m.add_cube(bone, "%s_hoop%d" % (name, k), p + v3(0, r, 0) + off, R, (2 * r + 0.05, 0.06, 2 * r + 0.05),
                   {"all": hoop, "+2": None, "-2": None})


def crate(m, bone, name, p, s=0.6, yaw=0.0, wood="dark_wood", strap="hull_light"):
    """Wooden crate with two straps."""
    p = v3(*p)
    R = ry(yaw)
    m.add_cube(bone, name, p + v3(0, s / 2, 0), R, (s, s, s), wood)
    for k, f in enumerate((-0.3, 0.3)):
        m.add_cube(bone, "%s_strap%d" % (name, k), p + v3(0, s / 2, 0) + R @ v3(s * f, 0, 0), R, (0.06, s + 0.02, s + 0.02),
                   {"all": strap, "+1": None, "-1": None})


def rope_coil(m, bone, name, p, r=0.32, rope="rope", turns=2):
    """Coiled rope lying flat on the deck."""
    p = v3(*p)
    for t in range(turns):
        rr = r - t * 0.09
        y = p[1] + 0.04 + t * 0.07
        for k in range(8):
            a0, a1 = 2 * math.pi * k / 8, 2 * math.pi * (k + 1) / 8
            m.beam(bone, "%s_%d_%d" % (name, t, k), (p[0] + math.cos(a0) * rr, y, p[2] + math.sin(a0) * rr),
                   (p[0] + math.cos(a1) * rr, y, p[2] + math.sin(a1) * rr), 0.08, rope, extend=0.03)


def fife_rail(m, bone, name, x, z, deck_y, half=0.95, wood="dark_wood", pin="hull_light", rope="rope"):
    """Square pin rail around a mast foot: four posts, the rail, belaying pins with rope falls."""
    top = deck_y + 0.62
    corners = [v3(x + sx * half, 0, z + sz * half) for sx, sz in ((1, 1), (-1, 1), (-1, -1), (1, -1))]
    for k, c in enumerate(corners):
        m.beam(bone, "%s_post%d" % (name, k), (c[0], deck_y, c[2]), (c[0], top + 0.05, c[2]), 0.12, wood)
        n = corners[(k + 1) % 4]
        m.beam(bone, "%s_rail%d" % (name, k), (c[0], top, c[2]), (n[0], top, n[2]), 0.1, wood, width=0.16, extend=0.06)
        for j in range(1, 4):
            q = c + (n - c) * (j / 4.0)
            m.add_cube(bone, "%s_pin%d_%d" % (name, k, j), (q[0], top + 0.12, q[2]), EYE, (0.05, 0.26, 0.05), pin)
            m.beam(bone, "%s_fall%d_%d" % (name, k, j), (q[0], top + 0.02, q[2]), (q[0] * 0.98 + x * 0.02, deck_y + 0.08, q[2]), 0.04, rope)


def bell(m, bone, name, p, metal="gold", wood="dark_wood"):
    """Ship's bell hanging in a small belfry."""
    p = v3(*p)
    for sx in (-1, 1):
        m.beam(bone, "%s_post_%d" % (name, sx > 0), p + v3(sx * 0.45, 0, 0), p + v3(sx * 0.45, 1.3, 0), 0.12, wood)
    m.beam(bone, name + "_beam", p + v3(-0.55, 1.3, 0), p + v3(0.55, 1.3, 0), 0.14, wood)
    m.add_cube(bone, name + "_roof", p + v3(0, 1.45, 0), EYE, (1.2, 0.12, 0.5), wood)
    m.add_cube(bone, name + "_bell", p + v3(0, 0.95, 0), EYE, (0.34, 0.36, 0.34), metal)
    m.add_cube(bone, name + "_lip", p + v3(0, 0.78, 0), EYE, (0.44, 0.08, 0.44), metal)


def amphora(m, bone, name, p, clay="hull_light", dark="dark_wood"):
    """Clay amphora standing on deck."""
    p = v3(*p)
    m.add_cube(bone, name + "_body", p + v3(0, 0.28, 0), EYE, (0.34, 0.4, 0.34), clay)
    m.add_cube(bone, name + "_foot", p + v3(0, 0.05, 0), EYE, (0.16, 0.1, 0.16), clay)
    m.add_cube(bone, name + "_neck", p + v3(0, 0.55, 0), EYE, (0.14, 0.18, 0.14), clay)
    m.add_cube(bone, name + "_rim", p + v3(0, 0.66, 0), EYE, (0.2, 0.05, 0.2), dark)


def bucket(m, bone, name, p, wood="hull_mid", hoop="iron"):
    p = v3(*p)
    m.add_cube(bone, name, p + v3(0, 0.17, 0), EYE, (0.3, 0.34, 0.3), {"all": wood, "+2": None})
    m.add_cube(bone, name + "_hoop", p + v3(0, 0.22, 0), EYE, (0.33, 0.05, 0.33), {"all": hoop, "+2": None, "-2": None})
