"""Shape and layout of the Crystal Airship (crystal_airship, "Le Grand Dirigeable de Cristal"), shared by the
model generator, the interior grid, the furniture and the texture.

MUST stay identical to CrystalLayout (Java), which uses the same formulas and numbers for the terrain probes,
the seats and the autopilot (checked by CrystalTest.matchesModelGenerator).

Ship-local coordinates, in blocks: x = lateral (+x = port), y = up (0 = the main deck), z = forward (+z = bow).
Measured on the reference sheet (side view: 0.13 block per pixel, see docs/CRYSTAL_PLAN.md): a hull of 48.6
blocks (51 with the beak, 55 with the aft spar and the floating crystal pods) and 12 wide, a cluster of seven
cream balloon lobes (a big central egg, a fore and an aft lobe on the axis, higher, four side lobes at the
corners, lower) over a big golden ring, a three-storey stern castle, engine nacelles on the aft sides, a round
stern engine, two slanted propeller pods under the stern, glowing blue crystals.
"""
import math

CELL = 0.5

# ---------------------------------------------------------------- balloon: a cluster of lobes
CY = 16.2                  # axis of the central lobe
# (name, cx, cy, cz, half width, half height, half length, a, b): sections are ellipses scaled by (1 - |t|^a)^b
LOBES = (
    ("c", 0.0, CY, -0.3, 7.6, 6.6, 15.8, 2.2, 0.5),
    ("f", 0.0, CY + 3.3, 14.6, 4.0, 3.55, 6.6, 2.2, 0.5),
    ("r", 0.0, CY + 3.6, -12.0, 4.8, 4.3, 8.6, 2.2, 0.5),
    ("fp", 5.9, CY + 1.1, 9.6, 4.0, 4.2, 5.4, 2.2, 0.5),
    ("fs", -5.9, CY + 1.1, 9.6, 4.0, 4.2, 5.4, 2.2, 0.5),
    ("rp", 5.9, CY + 1.1, -9.8, 4.1, 4.3, 6.0, 2.2, 0.5),
    ("rs", -5.9, CY + 1.1, -9.8, 4.1, 4.3, 6.0, 2.2, 0.5),
)
# golden straps round the lobes: (lobe, t along its half length)
STRAPS = (("f", -0.05), ("f", 0.62), ("c", -0.92), ("c", 0.6), ("c", 0.02), ("c", -0.52),
          ("r", 0.55), ("r", -0.62), ("fp", 0.1), ("fs", 0.1), ("rp", -0.1), ("rs", -0.1))
GIRDLE_AZ = 112.0          # the golden girdle round the central lobe (azimuth from the top), where the swags hang
MAST_Z = -0.3
MAST_BASE = CY + 6.6       # the top of the central lobe
MAST_TOP = 27.4
CROW_Y = MAST_BASE + 1.0   # the brass platform on the mast

# ---------------------------------------------------------------- the golden ring over the main deck
RING_Y = 5.5
RING_Z = -0.3
RING_R = 4.1               # outer radius
RING_W = 1.0               # width of its rim (radial)
RING_T = 1.0               # its thickness (across the ship)
PEDESTAL = (0.65, RING_Y - RING_R + 0.25)   # half width of the column, its top

# ---------------------------------------------------------------- hull
MAIN_DECK_Y = 0.0
HULL_HW = 6.0
BOW_Z = 25.6               # the stem at the forecastle
STERN_Z = -23.0            # the transom
BOW_PLAN = (26.6, 2.0, 0.6)     # plan: hw = HULL_HW * (1 - (z / s)^a)^b ahead of the middle
STERN_PLAN = (40.0, 2.5, 0.5)   # behind it
SHEER_WAIST = 1.0          # top of the bulwark of the main deck
SECTION_P = 2.6            # the bilge's roundness
TUMBLE = 0.02
SHELL = 0.4
# the keel line (z, y) from the transom to the head of the stem: deep, rounded belly, a clipper bow sweeping up
KEEL_PTS = ((-23.0, -4.4), (-21.5, -5.8), (-19.2, -7.0), (-15.3, -8.9), (-10.0, -9.9), (-5.0, -9.6), (0.0, -9.0), (5.1, -7.9),
            (11.6, -6.4), (15.9, -5.6), (19.2, -4.5), (22.3, -2.6), (24.3, -1.0), (25.4, 0.4), (26.1, 1.6))
BEAK = ((25.6, 0.9), (28.0, 0.75))   # (z, y) of the root and the tip of the carved beak under the forecastle

# decks
FORECASTLE_Y = 2.0
FORECASTLE_Z = 13.3        # from here to the bow
RAIL_H = 1.0
DECK_SLAB = 0.5
TURRET = (1.5, 10.0, 13.3, 4.3)        # half width, z0, z1, top of the crenellated turret on the main deck

# stern castle: storey 1 (on the main deck) and storey 2 (the cockpit), the green roof
CASTLE_Z = -10.1           # front of storey 1
L1_Y, L1_TOP = 0.0, 3.0
L2_Z = -14.0               # front of storey 2 (storey 1's roof in front of it is a terrace)
L2_Y, L2_TOP = 3.0, 5.8
ROOF_Z = (-23.8, -14.4)    # the green roof, overhanging
ROOF_Y = (5.8, 7.6)
CASTLE_FLARE = 0.25        # the castle's walls stand out of the hull's sides a little (overhang)

# the cockpit: the arched window facing the bow (x half width, sill, springing of the arch, crown)
ARCH = (2.4, 3.4, 4.5, 5.25)
HELM_Z = -15.9
PILOT_Z = -16.8

# ---------------------------------------------------------------- engines and crystals
NACELLE = (8.4, -2.3, -23.6, -9.2, 3.6)       # x (both sides), y, z0, z1, radius of the drum
NACELLE_EYE = (-18.7, 1.35)                    # z, radius of the crystal eye on the outer face
REAR_ENGINE = (-3.6, -23.0, -25.2, 3.6)       # y, z of its face on the transom, z of its rim, radius
PROP_PODS = (7.0, (-6.6, -5.0), (-10.0, -10.4))   # x (both sides), (y, z) of the root, (y, z) of the hub
PROP_BLADE = 4.2
BOTTOM_CRYSTAL = (0.3, -12.0, 3.1, -15.0)     # z, platform y, platform radius, tip y
HANGING_CRYSTALS = ((2.6, -6.4, 19.3), (-2.6, -6.4, 19.3), (0.0, -8.9, 10.0))
FRONT_POD = (0.0, 9.6, 24.6)
REAR_POD = (0.0, 14.8, -24.6)
POD_R = 2.0
CASTLE_CRYSTALS = ((4.9, 2.2, -9.0), (-4.9, 2.2, -9.0))   # crystal lamps on the rail at the castle's front corners


def lobe(name):
    for lb in LOBES:
        if lb[0] == name:
            return lb
    raise KeyError(name)


def lobe_scale(lb, z):
    t = (z - lb[3]) / lb[6]
    if abs(t) >= 1.0:
        return 0.0
    return (1.0 - abs(t) ** lb[7]) ** lb[8]


def lobe_point(lb, z, az_deg, out=0.0):
    """Point of a lobe's surface at z, azimuth (degrees from the top, + towards port), pushed out along the
    normal of the section by `out`."""
    s = lobe_scale(lb, z)
    w, h = lb[4] * s, lb[5] * s
    a = math.radians(az_deg)
    x, y = math.sin(a) * w, math.cos(a) * h
    if out:
        nx, ny = x / max(w, 1e-6) ** 2, y / max(h, 1e-6) ** 2
        n = math.hypot(nx, ny)
        if n > 1e-9:
            x, y = x + nx / n * out, y + ny / n * out
    return (lb[1] + x, lb[2] + y, z)


def inside_lobe(lb, x, y, z, inset=0.0):
    s = lobe_scale(lb, z)
    w, h = lb[4] * s - inset, lb[5] * s - inset
    if w <= 0 or h <= 0:
        return False
    return ((x - lb[1]) / w) ** 2 + ((y - lb[2]) / h) ** 2 <= 1.0


def inside_balloon(x, y, z, inset=0.0, skip=None):
    return any(inside_lobe(lb, x, y, z, inset) for lb in LOBES if lb[0] != skip)


# ---------------------------------------------------------------- hull
def _smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def hull_hw(z):
    """Half beam of the plan at z (at the bulwark)."""
    if z > BOW_Z + 0.75 or z < STERN_Z:
        return 0.0
    s, a, b = BOW_PLAN if z >= 0 else STERN_PLAN
    t = abs(z) / s
    if t >= 1.0:
        return 0.0
    return HULL_HW * (1.0 - t ** a) ** b


def _keel_slopes():
    p = KEEL_PTS
    n = len(p)
    d = [(p[i + 1][1] - p[i][1]) / (p[i + 1][0] - p[i][0]) for i in range(n - 1)]
    m = [d[0]] + [0.0 if d[i - 1] * d[i] <= 0 else (d[i - 1] + d[i]) / 2 for i in range(1, n - 1)] + [d[-1]]
    for i in range(n - 1):   # Fritsch-Carlson: no overshoot
        if d[i] == 0:
            m[i] = m[i + 1] = 0.0
            continue
        a, b = m[i] / d[i], m[i + 1] / d[i]
        s = a * a + b * b
        if s > 9:
            t = 3 / math.sqrt(s)
            m[i], m[i + 1] = t * a * d[i], t * b * d[i]
    return m


KEEL_SLOPES = _keel_slopes()


def keel_y(z):
    """Bottom of the hull (outside of the planking) at z; beyond the head of the stem: above everything."""
    p, m = KEEL_PTS, KEEL_SLOPES
    if z <= p[0][0]:
        return p[0][1]
    if z >= p[-1][0]:
        return 99.0
    i = 0
    while z > p[i + 1][0]:
        i += 1
    h = p[i + 1][0] - p[i][0]
    t = (z - p[i][0]) / h
    h00, h10, h01, h11 = 2 * t ** 3 - 3 * t ** 2 + 1, t ** 3 - 2 * t ** 2 + t, -2 * t ** 3 + 3 * t ** 2, t ** 3 - t ** 2
    return h00 * p[i][1] + h10 * h * m[i] + h01 * p[i + 1][1] + h11 * h * m[i + 1]


def deck_y(z):
    """Walkable open deck at z (the main deck, the forecastle)."""
    return FORECASTLE_Y if z >= FORECASTLE_Z else MAIN_DECK_Y


def sheer_y(z):
    """Top of the hull planking: the waist bulwark, the forecastle's bulwark (a smooth step)."""
    return SHEER_WAIST + (FORECASTLE_Y + RAIL_H - SHEER_WAIST) * _smooth((z - (FORECASTLE_Z - 0.6)) / 0.9)


def hull_x(z, y):
    """Half width of the outside of the hull at (z, y): a round bilge from the keel up to the bulwark, a slight
    tumblehome above it."""
    w = hull_hw(z)
    if w <= 0:
        return 0.0
    k = keel_y(z)
    if y < k:
        return 0.0
    if y <= SHEER_WAIST:
        eta = (y - k) / max(0.05, SHEER_WAIST - k)
        return w * (0.1 + 0.9 * (1.0 - (1.0 - eta) ** SECTION_P) ** 0.5)
    return w * (1.0 - TUMBLE * (y - SHEER_WAIST))


def inside_hull(x, y, z, inset=0.0):
    if y > sheer_y(z) or y < keel_y(z) + inset:
        return False
    return abs(x) <= hull_x(z, y) - inset


def castle_x(z, y):
    """Half width of the outside of the stern castle's walls (above the main deck): the hull's side at the
    bulwark, standing out a little (CASTLE_FLARE)."""
    return hull_x(z, SHEER_WAIST) + CASTLE_FLARE


def castle_top(z):
    """Top of the castle's walls at z (0 where there is no castle)."""
    if z > CASTLE_Z or z < STERN_Z:
        return 0.0
    if z > L2_Z:
        return L1_TOP
    return L2_TOP


# ---------------------------------------------------------------- engines
NACELLE_NOSE = (2.5, -14.6, -15.8)   # radius of the domed nose and its barrel, z where the barrel ends, z where the drum is full


def nacelle_r(z):
    """Radius of a side nacelle at z: a domed nose on a barrel, flaring into the big drum round the crystal eye, an
    iron tail."""
    x, y, z0, z1, r = NACELLE
    rn, zb, zd = NACELLE_NOSE
    if z > z1 or z < z0:
        return 0.0
    if z > z1 - rn:   # the dome
        t = (z - (z1 - rn)) / rn
        return rn * math.sqrt(max(0.0, 1.0 - t * t))
    if z > zb:        # the barrel
        return rn
    if z > zd:        # the flare
        return rn + (r - rn) * _smooth((zb - z) / (zb - zd))
    if z > z0 + 1.6:  # the drum, its aft edge rounded
        return r - 0.6 * _smooth((z0 + 2.6 - z) / 1.0)
    return r * 0.62   # the iron tail


def inside_nacelle(x, y, z, inset=0.0):
    nx, ny = NACELLE[0], NACELLE[1]
    r = nacelle_r(z) - inset
    if r <= 0:
        return False
    return (abs(x) - nx) ** 2 + (y - ny) ** 2 <= r * r


def pod_frame(side):
    """Root, hub and unit axis (towards the hub) of a slanted propeller pod under the stern (side +1 port)."""
    x, (y0, z0), (y1, z1) = PROP_PODS
    root = (side * (x - 0.6), y0, z0)
    hub = (side * x, y1, z1)
    d = [hub[i] - root[i] for i in range(3)]
    L = math.sqrt(sum(c * c for c in d))
    return root, hub, tuple(c / L for c in d)


if __name__ == "__main__":
    # values checked by CrystalTest.matchesModelGenerator
    for lb in LOBES[:3]:
        for z in (lb[3] - lb[6] * 0.5, lb[3], lb[3] + lb[6] * 0.8):
            print("{%d, %.6f, %.6f}," % (LOBES.index(lb), z, lobe_scale(lb, z)))
    for z, y in ((-20.0, -3.0), (-10.0, -6.0), (0.0, -8.5), (0.0, 0.5), (8.0, -3.0), (16.0, -2.0), (22.0, 1.5), (-16.0, 2.0)):
        print("{%s, %s, %.6f, %.6f, %.6f}," % (z, y, hull_x(z, y), keel_y(z), sheer_y(z)))
    for z in (-22.0, -15.0, -10.0):
        print("{%s, %.6f}," % (z, nacelle_r(z)))
