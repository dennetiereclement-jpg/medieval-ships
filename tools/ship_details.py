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


# ---------------------------------------------------------------- cabin furniture
def _box(m, bone, name, c, R, size, regions):
    return m.add_cube(bone, name, c, R, size, regions)


def rug(m, bone, name, p, w, l, yaw=0.0, region="rug"):
    """Carpet lying on the floor (w across, l along the local z axis)."""
    p = v3(*p)
    m.add_cube(bone, name, p + v3(0, 0.012, 0), ry(yaw), (w, 0.02, l), {"all": None, "+2": region}, stretch=True,
               u_dir=ry(yaw) @ v3(0, 0, 1), v_dir=ry(yaw) @ v3(1, 0, 0))


def table(m, bone, name, p, w, d, h=0.78, yaw=0.0, top="hull_light", legs="dark_wood"):
    p = v3(*p)
    R = ry(yaw)
    m.add_cube(bone, name + "_top", p + v3(0, h - 0.04, 0), R, (w, 0.08, d), {"all": legs, "+2": top})
    for k, (sx, sz) in enumerate(((1, 1), (-1, 1), (-1, -1), (1, -1))):
        q = p + R @ v3(sx * (w / 2 - 0.08), 0, sz * (d / 2 - 0.08))
        m.add_cube(bone, "%s_leg%d" % (name, k), q + v3(0, (h - 0.08) / 2, 0), R, (0.08, h - 0.08, 0.08), legs)


def chair(m, bone, name, p, facing, seat="hull_light", wood="dark_wood"):
    """Chair whose sitter looks along `facing` (yaw, radians; 0 = towards +z)."""
    p = v3(*p)
    R = ry(facing)
    m.add_cube(bone, name + "_seat", p + v3(0, 0.45, 0), R, (0.48, 0.07, 0.48), seat)
    m.add_cube(bone, name + "_back", p + R @ v3(0, 0.78, -0.22), R, (0.48, 0.62, 0.07), seat)
    for k, (sx, sz) in enumerate(((1, 1), (-1, 1), (-1, -1), (1, -1))):
        m.add_cube(bone, "%s_leg%d" % (name, k), p + R @ v3(sx * 0.19, 0.21, sz * 0.19), R, (0.06, 0.42, 0.06), wood)


def stool(m, bone, name, p, wood="dark_wood", top="hull_light"):
    p = v3(*p)
    m.add_cube(bone, name, p + v3(0, 0.4, 0), EYE, (0.4, 0.07, 0.4), top)
    for k, (sx, sz) in enumerate(((1, 1), (-1, 1), (-1, -1), (1, -1))):
        m.add_cube(bone, "%s_leg%d" % (name, k), p + v3(sx * 0.14, 0.19, sz * 0.14), EYE, (0.06, 0.38, 0.06), wood)


def chart_on_table(m, bone, name, p, yaw=0.0, region="chart", tool="iron"):
    """Sea chart spread on a table, with a pair of dividers."""
    p = v3(*p)
    m.add_cube(bone, name, p + v3(0, 0.006, 0), ry(yaw), (0.62, 0.012, 0.5), {"all": None, "+2": region}, stretch=True,
               u_dir=ry(yaw) @ v3(1, 0, 0), v_dir=ry(yaw) @ v3(0, 0, 1))
    m.beam(bone, name + "_divider_a", p + ry(yaw) @ v3(0.05, 0.02, 0.0), p + ry(yaw) @ v3(0.22, 0.02, 0.12), 0.025, tool)
    m.beam(bone, name + "_divider_b", p + ry(yaw) @ v3(0.05, 0.02, 0.0), p + ry(yaw) @ v3(0.25, 0.02, -0.06), 0.025, tool)


def candle(m, bone, name, p, metal="gold", wax="cloth_roll"):
    """Candlestick with a lit flame (glow)."""
    p = v3(*p)
    m.add_cube(bone, name + "_foot", p + v3(0, 0.02, 0), EYE, (0.14, 0.04, 0.14), metal)
    m.add_cube(bone, name + "_stem", p + v3(0, 0.12, 0), EYE, (0.05, 0.18, 0.05), metal)
    m.add_cube(bone, name + "_candle", p + v3(0, 0.27, 0), EYE, (0.06, 0.14, 0.06), wax)
    m.add_cube(bone, "glow_" + name + "_flame", p + v3(0, 0.37, 0), EYE, (0.04, 0.07, 0.04), "glow", stretch=True)


def candelabra(m, bone, name, p, metal="gold", wax="cloth_roll"):
    """Three-branch candelabra for the great table."""
    p = v3(*p)
    m.add_cube(bone, name + "_foot", p + v3(0, 0.03, 0), EYE, (0.2, 0.06, 0.2), metal)
    m.add_cube(bone, name + "_stem", p + v3(0, 0.2, 0), EYE, (0.06, 0.32, 0.06), metal)
    m.add_cube(bone, name + "_arms", p + v3(0, 0.36, 0), EYE, (0.42, 0.04, 0.05), metal)
    for k, x in enumerate((-0.19, 0.0, 0.19)):
        top = 0.48 if k == 1 else 0.43
        m.add_cube(bone, "%s_candle%d" % (name, k), p + v3(x, top - 0.05, 0), EYE, (0.05, 0.12, 0.05), wax)
        m.add_cube(bone, "glow_%s_flame%d" % (name, k), p + v3(x, top + 0.04, 0), EYE, (0.035, 0.06, 0.035), "glow", stretch=True)


def tableware(m, bone, name, p, yaw=0.0, metal="iron", glass="rope", plate="hull_light"):
    """Plates, goblets and a bottle on a table."""
    p = v3(*p)
    R = ry(yaw)
    for k, (x, z) in enumerate(((-0.18, 0.1), (0.2, -0.08))):
        m.add_cube(bone, "%s_plate%d" % (name, k), p + R @ v3(x, 0.01, z), R, (0.22, 0.02, 0.22), metal)
        m.add_cube(bone, "%s_goblet%d" % (name, k), p + R @ v3(x + 0.16, 0.06, z + 0.12), R, (0.05, 0.12, 0.05), "gold")
    m.add_cube(bone, name + "_bottle", p + R @ v3(0.0, 0.11, 0.18), R, (0.09, 0.22, 0.09), glass)
    m.add_cube(bone, name + "_bottle_neck", p + R @ v3(0.0, 0.26, 0.18), R, (0.04, 0.09, 0.04), glass)


def bookshelf(m, bone, name, p, yaw=0.0, w=1.0, h=1.9, d=0.36, wood="dark_wood", books="books"):
    """Bookshelf; its open front faces along `yaw` (0 = towards +z)."""
    p = v3(*p)
    R = ry(yaw)
    m.add_cube(bone, name, p + v3(0, h / 2, 0), R, (w, h, d), {"all": wood, "+3": books}, stretch=True,
               u_dir=R @ v3(1, 0, 0), v_dir=v3(0, -1, 0))
    m.add_cube(bone, name + "_crown", p + v3(0, h + 0.05, 0) + R @ v3(0, 0, 0.03), R, (w + 0.1, 0.1, d + 0.08), wood)


def bunk(m, bone, name, p, yaw=0.0, l=1.9, w=0.9, wood="dark_wood", bedding="bedding"):
    """Box bed along `yaw` (head towards -z local): frame, mattress with blanket and pillow."""
    p = v3(*p)
    R = ry(yaw)
    m.add_cube(bone, name + "_frame", p + v3(0, 0.22, 0), R, (w, 0.44, l), wood)
    m.add_cube(bone, name + "_mattress", p + v3(0, 0.5, 0), R, (w - 0.12, 0.14, l - 0.12), {"all": bedding, "+2": bedding},
               stretch=True, u_dir=R @ v3(0, 0, 1), v_dir=R @ v3(1, 0, 0))
    m.add_cube(bone, name + "_head", p + v3(0, 0.55, 0) + R @ v3(0, 0, -l / 2 + 0.04), R, (w, 1.1, 0.08), wood)
    m.add_cube(bone, name + "_foot", p + v3(0, 0.38, 0) + R @ v3(0, 0, l / 2 - 0.04), R, (w, 0.76, 0.08), wood)


def painting(m, bone, name, p, normal, w=0.8, h=0.6, region="painting"):
    """Framed painting on a wall whose inner side faces `normal` (horizontal unit vector)."""
    n = v3(*normal)
    n = n / np.linalg.norm(n)
    u = np.cross(v3(0, 1, 0), n)
    m.add_cube(bone, name, v3(*p) + n * 0.03, np.column_stack([u, v3(0, 1, 0), n]), (w, h, 0.05),
               {"all": "gold", "+3": region}, stretch=True, u_dir=u, v_dir=v3(0, -1, 0))


def weapon_rack(m, bone, name, p, normal, w=1.1, wood="dark_wood", metal="iron"):
    """Muskets and a sabre standing against a wall."""
    n = v3(*normal)
    n = n / np.linalg.norm(n)
    u = np.cross(v3(0, 1, 0), n)
    p = v3(*p)
    m.add_cube(bone, name + "_board", p + v3(0, 1.3, 0) + n * 0.05, np.column_stack([u, v3(0, 1, 0), n]), (w, 0.12, 0.1), wood)
    m.add_cube(bone, name + "_base", p + v3(0, 0.08, 0) + n * 0.12, np.column_stack([u, v3(0, 1, 0), n]), (w, 0.16, 0.22), wood)
    for k, t in enumerate(np.linspace(-0.38, 0.38, 4)):
        q = p + u * t * w / 1.1
        m.beam(bone, "%s_stock%d" % (name, k), q + n * 0.13 + v3(0, 0.12, 0), q + n * 0.1 + v3(0, 0.6, 0), 0.08, wood)
        m.beam(bone, "%s_barrel%d" % (name, k), q + n * 0.1 + v3(0, 0.6, 0), q + n * 0.06 + v3(0, 1.45, 0), 0.04, metal)


def hanging_lantern(m, bone, name, p, drop=0.35, frame="lantern", metal="iron"):
    """Lantern hanging from a ceiling beam by an iron rod (p = hook point)."""
    p = v3(*p)
    m.add_cube(bone, name + "_rod", p - v3(0, drop / 2, 0), EYE, (0.03, drop, 0.03), metal)
    c = p - v3(0, drop + 0.2, 0)
    m.add_cube(bone, name, c, EYE, (0.26, 0.36, 0.26), {"all": frame, "+2": metal, "-2": metal}, stretch=True)
    m.add_cube(bone, "glow_" + name, c, EYE, (0.17, 0.26, 0.17), "glow", stretch=True)


def globe(m, bone, name, p, sea="blue_paint", metal="gold"):
    """Terrestrial globe on a small stand."""
    p = v3(*p)
    m.add_cube(bone, name + "_stand", p + v3(0, 0.05, 0), EYE, (0.22, 0.1, 0.22), metal)
    m.add_cube(bone, name + "_ball", p + v3(0, 0.3, 0), EYE, (0.34, 0.34, 0.34), sea)
    m.add_cube(bone, name + "_ring", p + v3(0, 0.3, 0), EYE, (0.04, 0.44, 0.44), {"all": metal, "+1": None, "-1": None})
