"""Shape and layout of the Crystal Airship (crystal_airship, "Le Grand Dirigeable de Cristal"), shared by the
model generator, the interior grid, the furniture and the texture.

MUST stay identical to CrystalLayout (Java), which uses the same formulas and numbers for the terrain probes,
the seats and the autopilot (checked by CrystalTest.matchesModelGenerator).

Ship-local coordinates, in blocks: x = lateral (+x = port), y = up (0 = the main deck), z = forward (+z = bow).
Measured on the reference sheet (side view: 0.13 block per pixel, see docs/CRYSTAL_PLAN.md): a hull of 48.6
blocks (51 with the bowsprit, 56 with the aft spar and the floating crystal pods) and 12 wide, a banana keel, a
sheer sweeping up to a tall carved stem, a rounded stern; a cluster of seven cream balloon lobes (a big central
egg, a fore and an aft lobe on the axis, higher, four side lobes at the corners) low over the big golden ring,
whose top runs into its belly; a round stern castle in tiers (storey 1 inset from the hull's sides, storey 2 nearly as
wide and overhanging the stern, under a green mansard roof), ornate brass engines on the aft sides, a brass
gear medallion on the stern, two slanted propeller pods under the stern, glowing blue crystals.
"""
import math

CELL = 0.5

# ---------------------------------------------------------------- balloon: a cluster of lobes
CY = 14.0                  # axis of the central lobe (its top level with the sheet's, its belly just over the ring)
# (name, cx, cy, cz, half width, half height, half length, a, b): sections are ellipses scaled by (1 - |t|^a)^b
LOBES = (
    ("c", 0.0, CY, -0.3, 7.6, 6.9, 15.8, 2.4, 0.5),
    ("f", 0.0, CY + 2.9, 14.6, 4.2, 3.4, 6.6, 2.8, 0.5),
    ("r", 0.0, CY + 2.5, -12.0, 4.9, 4.4, 8.6, 2.8, 0.5),
    ("fp", 6.4, CY + 1.0, 9.6, 4.2, 4.3, 5.4, 2.8, 0.5),
    ("fs", -6.4, CY + 1.0, 9.6, 4.2, 4.3, 5.4, 2.8, 0.5),
    ("rp", 6.4, CY + 1.0, -9.8, 4.3, 4.4, 6.0, 2.8, 0.5),
    ("rs", -6.4, CY + 1.0, -9.8, 4.3, 4.4, 6.0, 2.8, 0.5),
)
# golden straps round the lobes: (lobe, t along its half length), each on the far side of its lobe's widest section as
# seen from the nearer end (from the ends a strap would read as a target ring or a flat disc's rim)
STRAPS = (("f", -0.35), ("c", 0.5), ("c", -0.12), ("c", -0.55),
          ("r", 0.45), ("fp", -0.4), ("fs", -0.4), ("rp", 0.4), ("rs", 0.4))
MERIDIANS = {}             # meridian straps (lobe: azimuths): none, they read as pie slices from the ends
PUFF = (0.045,)            # the skin puffs out between the straps (fraction of the radius)
GIRDLE_AZ = 112.0          # the golden girdle round the central lobe (azimuth from the top), where the swags hang
MAST_Z = -0.3
MAST_BASE = CY + 6.9       # the top of the central lobe
MAST_TOP = MAST_BASE + 4.6
CROW_Y = MAST_BASE + 1.0   # the brass platform on the mast

# ---------------------------------------------------------------- the golden ring over the main deck
RING_Y = 5.4
RING_Z = -0.3
RING_R = 4.1               # outer radius (its top runs into the balloon's belly)
RING_W = 1.15              # width of its rim (radial)
RING_T = 1.0               # its thickness (across the ship)
PEDESTAL = (0.65, RING_Y - RING_R + 0.25)   # half width of the column, its top

# ---------------------------------------------------------------- hull
MAIN_DECK_Y = 0.0
HULL_HW = 6.0
BOW_Z = 25.6               # the stem at the forecastle
STERN_Z = -23.0            # the transom
BOW_PLAN = (26.6, 2.0, 0.6)     # plan: hw = HULL_HW * (1 - (z / s)^a)^b ahead of the middle
STERN_PLAN = (40.0, 2.5, 0.5)   # behind it
STERN_ROUND = (-18.6, 2.5)      # the stern rounds off in plan from this z to STERN_Z: hw *= (1 - u^p)^(1/p)
SHEER_WAIST = 1.0          # top of the bulwark of the main deck
SHEER_FWD = (8.5, 14.0, 1.45)   # the sheer sweeps up to the forecastle between these z, by this much...
SHEER_BOW = 0.85                # ... and on up to the stem
SHEER_AFT = 0.0                 # a rise aft, into the castle (z -3 .. -10): none, the castle rises there
SECTION_P = 1.6            # the bilge's roundness (the sections narrow to the keel)
TUMBLE = 0.02
SHELL = 0.4
# the keel line (z, y) from the stern to the head of the stem: a banana keel, deepest amidships, a full cut-back forefoot
KEEL_PTS = ((-23.0, -6.2), (-21.5, -7.2), (-19.5, -7.85), (-16.0, -8.35), (-12.0, -8.7), (-7.0, -9.05), (-2.0, -9.3), (3.0, -9.4),
            (8.0, -8.9), (13.0, -7.8), (17.0, -6.2), (20.5, -4.2), (23.0, -2.0), (24.8, 0.2), (25.8, 2.0), (26.3, 3.4))
STEM_HEAD = (26.0, 4.6)    # (z, top) of the carved stem-head post with its gilded volute
BOWSPRIT = ((24.6, 0.55), (28.3, 1.35), 0.7)   # (z, y) of its heel and its tip, its square side
BEAK = ((24.6, 0.55), (28.3, 1.35))            # kept for the pod's rope: the bowsprit

# decks
FORECASTLE_Y = 2.0
FORECASTLE_Z = 13.3        # from here to the bow
RAIL_H = 1.0
DECK_SLAB = 0.5
TURRET = (1.5, 10.0, 13.3, 4.0)        # half width, z0, z1, top of the lookout on the main deck (a moulded cap)

# stern castle in tiers, round at the stern: storey 1 (on the main deck, inset from the hull's sides), storey 2 (the cockpit,
# overhanging the stern), a green mansard roof over it (solid in the grid, its flat top walkable), the crest on its gable
CASTLE_Z = -10.1           # front of storey 1
L1_Y, L1_TOP = 0.0, 3.0
L2_Z = -14.0               # front of storey 2 (storey 1's roof in front of it is a terrace)
L2_Y, L2_TOP = 3.0, 6.4
CASTLE_INSET = (0.3, 0.45) # storeys 1 and 2: inset of their walls from the hull's side (storey 2 nearly as wide, as on
                           # the sheet's back view)
CASTLE1_ROUND = (STERN_ROUND[0] + 0.15, 2.2)   # storey 1 rounds off in plan from this z to STERN1_END (exponent)
CASTLE2_ROUND = (5.0, 2.1)                     # storey 2: over this length before STERN2_Z (exponent): a round stern
CASTLE2_TUCK = 0.45        # storey 2's round back is tucked in by up to this much more towards its stern (the tiers step)
STERN1_END = -22.75        # the stern of storey 1 (inside the hull's rounded stern)
STERN2_Z = -23.9           # the stern of storey 2 (it overhangs the hull's stern)
# the green mansard roof over storey 2: its eave's overhang past the walls, its inset at the top (from the walls), its
# flat top's height, the eave's height (the cornice, under the cockpit's ceiling: a tall roof sloping in on every side)
MANSARD = (0.2, 1.0, 8.0, 5.85)
ROOF_Y = (L2_TOP, MANSARD[2])   # the roof over the cockpit's ceiling (solid in the grid) and its top
CREST_Y = 9.5              # top of the gilded scroll crest at the gable's top
ENSIGN = (MANSARD[3], 4.3)  # the ensign boom aft from storey 2's stern at the cornice's height: its height, its length
DECK_SLAB_C = 0.5
BALCONY = (0.35, 0.8)      # the stern balcony round storey 1's stern: its overhang on the sides, aft

# the cockpit: the arched window facing the bow (x half width, sill, springing of the arch, crown)
ARCH = (2.4, 3.3, 4.6, 5.85)
HELM_Z = -15.9
PILOT_Z = -16.8

# ---------------------------------------------------------------- engines and crystals
NACELLE = (7.5, -2.3, -24.4, -9.6, 3.1)       # x (both sides), y, z0 (the end of the iron cap), z1 (the helmet's nose), radius
NACELLE_EYE = (-18.0, 1.7)                     # z, radius of the glowing crystal eye on the outer face
MEDALLION = (-2.5, -23.0, 2.25)                # y, z of its face, radius (its dark rim): the gear medallion on the stern,
                                               # tucked under the stern gallery
PROP_PODS = (7.0, (-6.6, -5.0), (-10.0, -10.4))   # x (both sides), (y, z) of the root, (y, z) of the hub
PROP_BLADE = 4.0
BOTTOM_CRYSTAL = (0.3, -12.0, 3.1, -15.0)     # z, platform y, platform radius, tip y
HANGING_CRYSTALS = ((2.0, -5.8, 20.4), (-2.0, -5.8, 20.4), (0.0, -10.2, 10.0))
FRONT_POD = (0.0, 7.2, 24.4)
REAR_POD = (0.0, 12.9, -25.4)    # high over the stern, well aft of the roof
POD_R = 2.0
CASTLE_CRYSTALS = ((4.6, 2.2, -9.0), (-4.6, 2.2, -9.0))   # crystal lamps on the rail at the castle's front corners


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


def lobe_strap_z(lb):
    """z of the straps round a lobe, with its two ends."""
    zs = [lb[3] + lb[6] * t for name, t in STRAPS if name == lb[0]]
    return sorted([lb[3] - lb[6]] + zs + [lb[3] + lb[6]])


def lobe_puff(lb, z):
    """The skin puffs out between the straps, a soft crease under each strap (a factor of the section's radii; the
    model only: the collisions and the probes use the plain lobes)."""
    zs = lobe_strap_z(lb)
    for a, b in zip(zs, zs[1:]):
        if a <= z <= b:
            t = (z - a) / max(1e-6, b - a)
            if a == zs[0] and b == zs[-1]:
                return 1.0
            if a == zs[0]:        # from the nose to the first strap
                return 1.0 + PUFF[0] * 0.8 * math.sin(math.pi / 2 * (1.0 - t)) ** 0.8
            if b == zs[-1]:       # from the last strap to the tail
                return 1.0 + PUFF[0] * 0.8 * math.sin(math.pi / 2 * t) ** 0.8
            return 1.0 + PUFF[0] * math.sin(math.pi * t) ** 0.8
    return 1.0


def lobe_point(lb, z, az_deg, out=0.0, puff=True):
    """Point of a lobe's surface at z, azimuth (degrees from the top, + towards port), pushed out along the
    normal of the section by `out`."""
    s = lobe_scale(lb, z) * (lobe_puff(lb, z) if puff else 1.0)
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


def plan_hw(z):
    """Half beam of the plan at z before the stern is rounded off."""
    if z > BOW_Z + 0.75:
        return 0.0
    s, a, b = BOW_PLAN if z >= 0 else STERN_PLAN
    t = abs(z) / s
    if t >= 1.0:
        return 0.0
    return HULL_HW * (1.0 - t ** a) ** b


def stern_round(z, z_end, z0=None, p=None):
    """Factor rounding a plan off between z0 and its end z_end (a superellipse quarter: a rounded stern)."""
    z0 = STERN_ROUND[0] if z0 is None else z0
    p = STERN_ROUND[1] if p is None else p
    if z >= z0:
        return 1.0
    if z <= z_end:
        return 0.0
    u = (z0 - z) / (z0 - z_end)
    return (1.0 - u ** p) ** (1.0 / p)


def hull_hw(z):
    """Half beam of the plan at z (at the bulwark): a rounded stern."""
    if z < STERN_Z:
        return 0.0
    return plan_hw(z) * stern_round(z, STERN_Z)


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
    """Top of the hull planking: a sheer sweeping up from the waist to the forecastle and on to the stem, rising a
    little aft into the castle."""
    z0, z1, rise = SHEER_FWD
    y = SHEER_WAIST + rise * _smooth((z - z0) / (z1 - z0))
    if z > z1:
        y += SHEER_BOW * min(1.0, (z - z1) / (BOW_Z - z1)) ** 1.4
    if z < -3.0:
        y += SHEER_AFT * _smooth((-3.0 - z) / 7.0)
    return y


def band_y(z):
    """Top of the green band of the lower hull (under the gallery): level amidships, sweeping up along the forefoot
    towards the stem."""
    k = keel_y(z)
    return min(max(-4.0, k + 1.7), sheer_y(z) - 1.0)


def band_low(z):
    """Bottom of the green band: the dark brown strakes along the keel below it."""
    k = keel_y(z)
    return k + 0.38 * (band_y(z) - k)


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


def castle1_x(z):
    """Half width of the outside of storey 1's walls: the hull's plan, inset (0 aft of its stern)."""
    if z > CASTLE_Z or z < STERN_Z:
        return 0.0
    return max(0.0, (plan_hw(z) - CASTLE_INSET[0]) * stern_round(z, STERN1_END, CASTLE1_ROUND[0], CASTLE1_ROUND[1]))


def castle2_x(z):
    """Half width of the outside of storey 2's walls: nearly as wide as storey 1, round at the stern (its round back tucked
    in a little, so the tiers step), rounded off further aft (it overhangs storey 1's stern)."""
    if z > L2_Z or z < STERN2_Z:
        return 0.0
    tuck = CASTLE2_TUCK * _smooth((STERN2_Z + CASTLE2_ROUND[0] - z) / CASTLE2_ROUND[0])
    return max(0.0, (plan_hw(z) - CASTLE_INSET[1] - tuck) * stern_round(z, STERN2_Z, STERN2_Z + CASTLE2_ROUND[0], CASTLE2_ROUND[1]))


def castle_x(z, y):
    """Half width of the outside of the stern castle's walls at z and height y (storey 1 below its floor slab,
    storey 2 above; the slab between them is as wide as either)."""
    if y < L1_TOP - DECK_SLAB_C:
        return castle1_x(z)
    if y < L1_TOP:
        return max(castle1_x(z), castle2_x(z))
    return castle2_x(z)


def balcony_x(z):
    """Half width of the stern balcony round storey 1's stern, on the hull's stern bulwark (0 forward of it)."""
    if z > STERN_ROUND[0] + 0.5:
        return 0.0
    return max(0.0, (plan_hw(z) + BALCONY[0]) * stern_round(z, STERN_Z - BALCONY[1], STERN_ROUND[0] - 0.3))


def castle_top(z):
    """Top of the castle's walls at z (0 where there is no castle)."""
    if z > CASTLE_Z or z < STERN2_Z:
        return 0.0
    if z > L2_Z:
        return L1_TOP
    return L2_TOP


# ---------------------------------------------------------------- engines
NACELLE_NOSE = (2.4, -13.6, -15.0)   # radius of the brass helmet and its neck, z where the neck ends, z where the drum is full
NACELLE_TAIL = (-20.4, -23.0, 1.2, 0.75)  # z where the drum starts tapering aft, z where the iron drum starts, its radius,
                                          # the radius of its flat end (the grille)


def nacelle_r(z):
    """Radius of a side nacelle at z: a domed brass helmet on a neck, flaring into the big drum round the crystal eye,
    tapering aft into a small iron drum narrowing to its flat end (the grille)."""
    x, y, z0, z1, r = NACELLE
    rn, zb, zd = NACELLE_NOSE
    za, zc, rc, re = NACELLE_TAIL
    if z > z1 or z < z0:
        return 0.0
    if z > z1 - rn:   # the helmet's dome
        t = (z - (z1 - rn)) / rn
        return rn * math.sqrt(max(0.0, 1.0 - t * t))
    if z > zb:        # the neck
        return rn
    if z > zd:        # the flare
        return rn + (r - rn) * _smooth((zb - z) / (zb - zd))
    if z > za:        # the drum
        return r
    if z > zc:        # its aft edge, rounded
        return r - (r - rc) * _smooth((za - z) / (za - zc))
    t = (zc - z) / (zc - z0)   # the iron drum, narrowing to its flat end
    return rc + (re - rc) * t ** 1.5


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
    for z, y in ((-20.0, -3.0), (-10.0, -6.0), (0.0, -8.5), (0.0, 0.5), (8.0, -3.0), (16.0, -2.0), (22.0, 1.5), (-16.0, 2.0),
                 (-22.5, -2.0), (11.0, 0.5), (25.0, 2.0), (-7.0, 1.0)):
        print("{%s, %s, %.6f, %.6f, %.6f}," % (z, y, hull_x(z, y), keel_y(z), sheer_y(z)))
    for z in (-24.0, -22.0, -15.0, -10.0):
        print("{%s, %.6f}," % (z, nacelle_r(z)))
    for z, y in ((-12.0, 1.0), (-20.0, 4.0), (-22.5, 1.0), (-23.5, 4.0), (-18.0, 2.7)):
        print("{%s, %s, %.6f}," % (z, y, castle_x(z, y)))
    print("mansard {%s, %s, %s, %s}, crest %s, ensign {%s, %s}" % (MANSARD + (CREST_Y,) + ENSIGN))
