"""Shape and layout of the Rustic Skyskiff (rustic_skiff), shared by the model generator, the interior grid
and the texture.

MUST stay identical to SkiffLayout (Java), which uses the same formulas and numbers for the terrain probes,
the seats and the autopilot (checked by SkiffTest.matchesModelGenerator).

Ship-local coordinates, in blocks: x = lateral (+x = port), y = up (0 = the fore deck and the cabin floor),
z = forward (+z = bow). Measured on the reference sheet (side view, 0.1 block per pixel of the sheet, see
docs/SKIFF_PLAN.md): a long, banana-shaped patched hull of 26 blocks (bow head to transom), 8 wide in its
body and narrowing into a raised bow, a heavy square beam of 4 blocks before the bow, the cabin with the
pilot deck on its roof (3 blocks above the deck), the big tattered canvas roof on splayed poles (apex 11.8
above the deck, its corners pulled up to the poles' tops like a pagoda), four telescoping tubes 7 to 8.5
blocks long at the stern round a carved post, a stepped keel ending in a long spike under the stern half
(the "spinning top" of the front and back views) and four canvas wings hanging under the sides, seen
edge-on from the front (the rear ones 11 blocks under the deck).
"""
import math

CELL = 0.5

# ---------------------------------------------------------------- hull
DECK_Y = 0.0              # the open fore deck and the cabin floor
HULL_BOW_Z = 13.4         # the head of the stem
HULL_STERN_Z = -13.0      # the transom
HULL_HW = 4.0             # half beam of the body (at the waist)
TRANSOM_HW = 3.3          # half beam at the transom
STERN_TAPER = (-4.0, 9.0)  # the body narrows from this z over that many blocks to the transom
BOW_ROOT_Z = 2.0          # the narrow bow part: hw = BOW_HW (1 - t^2)^0.6 from here (t = 0) to the stem (t = 1)
BOW_HW = 2.6
SHOULDER = (3.5, 6.5)     # the body blends into the narrow bow between these z (the step of the top view)
SHEER_WAIST = 1.0         # top of the bulwark of the fore deck (its rail cap above)
BOW_SHEER = 2.8           # the sheer sweeps up to the bow head
BOW_RISE_Z = 4.0          # ... from here
# section from the keel (eta 0) to the waist (eta 1), as a fraction of the half beam: a flat floor rounding up from a to a
# chine (eta ce, fraction cf), then a straight, slightly full flank to the waist: the bilge narrows just below the wale
# (the spinning top of the front and back views) and the hold keeps its floor
SECTION = (0.07, 0.16, 0.47, 0.8)   # a, ce, cf, q: f = a + (cf - a)(1 - (1 - eta/ce)^2) below the chine,
                                    # cf + (1 - cf)((eta - ce)/(1 - ce))^q above it
FLARE = 0.03              # the sides flare out a little above the waist
SHELL = 0.4               # thickness of the planking (interior grid)
# the keel line (z, y): deep amidships, rising in a long curve to the raised bow head; aft, a little rise
# under the transom; monotone cubic through these
KEEL_PTS = ((-13.0, -2.3), (-12.4, -2.75), (-11.0, -3.05), (-8.0, -3.15), (-4.0, -3.2), (0.0, -3.15), (3.0, -3.0), (5.5, -2.7),
            (7.5, -2.3), (9.5, -1.5), (11.0, -0.6), (12.2, 0.3), (13.0, 1.2), (13.4, 2.0))
BOW_STEPS = ((10.0, 0.5), (11.5, 1.0))   # the bow's floor steps up (z from which, height): the lean-to's raised floor
BOW_HEAD = (2.95, 13.55)  # (y, z) of the top of the stem head
BOWSPRIT = ((2.7, 12.9), (2.85, 17.2))   # (y, z) of the heel and the tip of the heavy, square bow beam (horizontal)

# ---------------------------------------------------------------- cabin, pilot deck, hold
CABIN_FRONT_Z = -3.0      # outer face of the cabin's front wall (the hull sides rise to the pilot deck aft of it)
PILOT_Y = 3.0             # the pilot deck on the cabin roof
DECK_SLAB = 0.5
PILOT_HW = 4.9            # the pilot deck overhangs the hull sides (beams, brackets under it)
PILOT_Z = (-13.45, -2.6)  # its aft and fore edges
OUTRIGGER = 0.8           # carved outriggers stick out this far beyond its sides (under its edge beams)
PARTITION_Z = -7.75       # the wall between the cabin's common room and the bedroom (centre)
HOLD_Y = -2.5             # the storage hold under the decks
HOLD_Z = (-10.5, 4.5)
HELM_Z = -4.3             # the wheel on the pilot deck, facing the bow
PILOT_STAND_Z = -5.1      # where the pilot stands behind it
RAIL_H = 1.5              # balustrade of the pilot deck (chest high: no jumping over it in flight)

# ---------------------------------------------------------------- the canvas roof (a tent on splayed poles)
CANOPY_Z = -9.0           # its centre (the king post)
APEX_Y = 11.8             # top of the canvas at the king post (its finial above)
KING_TOP = 12.6
POLE_FEET = ((4.25, -3.35), (4.25, -12.75))       # (|x|, z) of the corner poles' feet on the pilot deck
POLE_TOPS = ((4.869, 9.5, -1.5), (4.869, 9.5, -16.5))  # (|x|, y, z) of their tops: the roof's corners (they splay out)
POLE_TIP = 0.9            # the poles stick out beyond the canvas (the roof's corner peaks)
PILLARS = ((2.75, -4.25), (2.75, -12.25))  # (|x|, z) of the four thick posts of the pilot post, up through the canvas
PILLAR_W = 0.62
EAVE_HALF = (5.6, 8.6)    # half width and half length of the roof at its eaves (superellipse plan)
EAVE_N = 5.0
EAVE_Y = 9.5              # height of the eaves at the corner poles: the cloth is pulled up to the poles' tops
EAVE_SAG = 1.6            # the edges sag between the poles (a pagoda: the corners flick up)
EAVE_SAG_POW = 0.8        # how quickly the edge drops away from a corner (below 1: a sharp corner peak)
EAVE_PINCH = 0.08         # ... and are drawn in between them (the cloth pulled to the pole tops: a concave plan)
ROOF_POW = 2.0            # profile of the roof from the apex to the eaves: steep at the top, flat at the eaves
FRINGE = (0.6, 3.3)       # length range of the torn tongues of cloth hanging from the eaves
# the long inclined derricks at the stern (foot on the pilot deck's aft corners, tip beyond the stern)
DERRICKS = (((2.9, PILOT_Y, -12.9), (4.3, 11.6, -18.6)),)

# ---------------------------------------------------------------- the stern tubes
# four telescoping tubes round a carved post on the transom: x, y, radius at the root (each of the three lengths is
# TUBE_STEP wider than the one before, an iron collar at every step), z of the mouth (the upper ones the longest);
# the mouths are flared bronze bells round a dark, hollow throat
TUBES = ((1.1, 2.45, 0.44, -21.2), (-1.1, 2.45, 0.44, -21.2), (1.15, 1.1, 0.42, -19.8), (-1.15, 1.1, 0.42, -19.8))
TUBE_Z0 = -12.7           # the tubes' roots, inside the transom
TUBE_STEP = 0.07          # how much wider each length of a tube is than the one before
TUBE_BELL = 1.3           # the mouth's bell: radius over the last length's
TUBE_END = min(t[3] for t in TUBES)   # the farthest mouth
STERN_POST = (-13.4, 0.0, 2.45)   # z, bottom and top of the carved post between the tubes (stacked rings)

# ---------------------------------------------------------------- the canvas wings (hanging under the sides)
# each: name, root (x, y, z) on the hull, top corner (end of the upper spar), tip (lowest point); the canvas
# is stretched between the upper spar and the leading spar (root -> tip), its free edge scalloped between ribs
# the membranes hang nearly parallel to the hull's sides: from the front and the back they are seen edge-on, thin
# spars hanging about 3.5 blocks from the centre line (the side view is unchanged)
WINGS = (
    ("wing_fore", (2.6, -1.8, -0.6), (3.9, -4.6, -7.4), (3.4, -9.0, -6.4)),
    ("wing_aft", (2.45, -1.2, -11.9), (3.8, -1.7, -18.6), (3.4, -11.0, -14.2)),
)
WING_RIBS = (0.4, 0.75)         # rib tips along the free edge (fraction from the top corner to the tip)
WING_SCALLOP = 0.3              # depth of the hollows of the free edge between two ribs (fraction of their distance)
WING_BILLOW = 0.35              # the canvas bellies out between the spars (blocks)


def _smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


# ---------------------------------------------------------------- hull
def body_hw(z):
    """Half beam of the wide body at z (constant forward, tapering aft to the transom)."""
    z0, length = STERN_TAPER
    return HULL_HW - (HULL_HW - TRANSOM_HW) * _smooth((z0 - z) / length)


def bow_hw(z):
    """Half beam of the narrow bow part."""
    t = (z - BOW_ROOT_Z) / (HULL_BOW_Z - BOW_ROOT_Z)
    if t >= 1.0:
        return 0.0
    if t <= 0.0:
        return BOW_HW
    return BOW_HW * (1.0 - t * t) ** 0.6


def hull_hw(z):
    """Half beam at z (at the waist): the body, blending into the narrow raised bow over the shoulder."""
    if z > HULL_BOW_Z or z < HULL_STERN_Z:
        return 0.0
    s = _smooth((z - SHOULDER[0]) / (SHOULDER[1] - SHOULDER[0]))
    return body_hw(z) * (1.0 - s) + bow_hw(z) * s


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
    """Bottom of the hull (outside of the keel planking) at z."""
    p, m = KEEL_PTS, KEEL_SLOPES
    if z <= p[0][0]:
        return p[0][1]
    if z >= p[-1][0]:
        return p[-1][1]
    i = 0
    while z > p[i + 1][0]:
        i += 1
    h = p[i + 1][0] - p[i][0]
    t = (z - p[i][0]) / h
    h00, h10, h01, h11 = 2 * t ** 3 - 3 * t ** 2 + 1, t ** 3 - 2 * t ** 2 + t, -2 * t ** 3 + 3 * t ** 2, t ** 3 - t ** 2
    return h00 * p[i][1] + h10 * h * m[i] + h01 * p[i + 1][1] + h11 * h * m[i + 1]


def sheer_y(z):
    """Top of the hull planking: the low bulwark of the fore deck sweeping up to the bow head; aft of the cabin's
    front wall the sides rise to the pilot deck (the cabin's walls)."""
    if z <= CABIN_FRONT_Z:
        return PILOT_Y
    return SHEER_WAIST + (BOW_SHEER - SHEER_WAIST) * _smooth((z - BOW_RISE_Z) / (HULL_BOW_Z - BOW_RISE_Z)) ** 1.25


def deck_y(z):
    """The walkable floor of the open fore deck at z (it steps up twice under the bow's lean-to)."""
    y = DECK_Y
    for z0, h in BOW_STEPS:
        if z > z0:
            y = h
    return y


def waist_y(z):
    """Where the rounded bottom meets the straight (flaring) side: the waist, or a little above the keel at the bow."""
    return max(SHEER_WAIST, keel_y(z) + 0.6)


def hull_x(z, y):
    """Half width of the outside of the hull at (z, y): a rounded V from the keel to the waist, the sides flaring
    out a little above it."""
    w = hull_hw(z)
    if w <= 0:
        return 0.0
    k = keel_y(z)
    if y < k:
        return 0.0
    top = waist_y(z)
    if y <= top:
        a, ce, cf, q = SECTION
        eta = (y - k) / (top - k)
        if eta <= ce:
            return w * (a + (cf - a) * (1.0 - (1.0 - eta / ce) ** 2))
        return w * (cf + (1.0 - cf) * ((eta - ce) / (1.0 - ce)) ** q)
    return w * (1.0 + FLARE * (y - top))


def inside_hull(x, y, z, inset=0.0):
    if y > sheer_y(z) or y < keel_y(z) + inset:
        return False
    return abs(x) <= hull_x(z, y) - inset


# ---------------------------------------------------------------- canvas roof
def eave_radius(theta):
    """Distance from the roof's axis to its eaves in the direction theta (0 = port, pi/2 = bow): a superellipse
    plan drawn in between the corner poles."""
    a, b = EAVE_HALF
    c, s = abs(math.cos(theta)), abs(math.sin(theta))
    r = 1.0 / ((c / a) ** EAVE_N + (s / b) ** EAVE_N) ** (1.0 / EAVE_N)
    return r * (1.0 - EAVE_PINCH * math.sin(math.pi * edge_fraction(theta)) ** 1.5)


def corner_angles():
    """Azimuths of the four corner poles' tops about the roof's axis."""
    out = []
    for sx in (1, -1):
        for (x, y, z) in POLE_TOPS:
            out.append(math.atan2(z - CANOPY_Z, sx * x))
    return out


def edge_fraction(theta):
    """Where the azimuth theta falls on the edge between two corner poles: 0 at a pole, 1 at the next one."""
    angs = sorted(a % (2 * math.pi) for a in corner_angles())
    t = theta % (2 * math.pi)
    for i in range(len(angs)):
        a0 = angs[i]
        a1 = angs[(i + 1) % len(angs)] + (2 * math.pi if i == len(angs) - 1 else 0.0)
        tt = t if t >= a0 else t + 2 * math.pi
        if a0 <= tt <= a1:
            return (tt - a0) / (a1 - a0)
    return 0.0


def eave_drop(theta):
    """How far the eave hangs below EAVE_Y in direction theta: 0 at the poles, EAVE_SAG midway between them."""
    return EAVE_SAG * math.sin(math.pi * edge_fraction(theta)) ** EAVE_SAG_POW


def roof_azimuths(n):
    """n azimuths around the roof, the four corner poles among them, the edges divided by their angular spans."""
    angs = sorted(a % (2 * math.pi) for a in corner_angles())
    spans = [(angs[(i + 1) % 4] - angs[i]) % (2 * math.pi) for i in range(4)]
    counts = [max(2, round(n * sp / (2 * math.pi))) for sp in spans]
    counts[counts.index(max(counts))] += n - sum(counts)
    out = []
    for i in range(4):
        out += [angs[i] + spans[i] * k / counts[i] for k in range(counts[i])]
    return out + [out[0] + 2 * math.pi]


def roof_point(theta, t):
    """Point of the canvas roof at azimuth theta (0 = port, pi/2 = bow) and fraction t from the apex (0) to the
    eaves (1): steep near the king post, flattening towards the eaves, drooping between the poles."""
    r = eave_radius(theta) * t
    ye = EAVE_Y - eave_drop(theta)
    y = ye + (APEX_Y - ye) * (1.0 - t) ** ROOF_POW
    return (r * math.cos(theta), y, CANOPY_Z + r * math.sin(theta))


# ---------------------------------------------------------------- wings
def wing_frame(wing, side):
    """(root, top, tip) of a wing on a side (+1 port, -1 starboard)."""
    name, root, top, tip = wing
    f = lambda p: (side * p[0], p[1], p[2])  # noqa: E731
    return f(root), f(top), f(tip)


def lerp3(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def wing_edge(wing, side, f):
    """Point of the free edge of a wing at fraction f from the top corner (0) to the tip (1), before the scallops."""
    root, top, tip = wing_frame(wing, side)
    return lerp3(top, tip, f)


# the stepped keel under the stern half (the inverted pyramid of the front and back views): tiers (half width, top,
# bottom, aft z, fore z), each narrower than the one above, and the long iron-shod spike under the lowest one
KEEL_TIERS = ((1.45, -2.6, -3.95, -12.55, -7.3), (1.0, -3.95, -4.85, -12.1, -8.2), (0.6, -4.85, -5.75, -11.6, -9.1))
SKID_TOP = (-5.75, -10.35)   # (y, z) of the head of the spike (under the lowest tier)
SKID_TIP = (-9.5, -10.8)     # (y, z) of its point


def roof_y(x, z):
    """Height of the canvas over the point (x, z) of the plan (its eave's height beyond the eaves)."""
    th = math.atan2(z - CANOPY_Z, x)
    r = math.hypot(x, z - CANOPY_Z)
    return roof_point(th, min(1.0, r / eave_radius(th)))[1]


def pillar_top(fx, fz):
    """Height of the canvas over a pillar (the pillar goes on through it to its cap)."""
    return roof_y(fx, fz)


def lowest_y():
    """The lowest point: the tip of a rear wing (its spike), lower than the keel spike."""
    return min(min(w[3][1] for w in WINGS) - 0.25, SKID_TIP[0])


if __name__ == "__main__":
    # values checked by SkiffTest.matchesModelGenerator
    for z, y in ((-12.5, -2.0), (-8.0, -3.0), (0.0, -2.5), (0.0, 0.5), (5.0, -2.0), (9.0, 0.5), (12.0, 1.5), (-5.0, 2.0)):
        print("{%s, %s, %.6f, %.6f, %.6f}," % (z, y, hull_x(z, y), keel_y(z), sheer_y(z)))
    for th, t in ((0.0, 1.0), (1.0, 0.5), (2.5, 1.0), (4.0, 0.8), (5.5, 0.95)):
        print("{%s, %s, %s}," % (th, t, ", ".join("%.6f" % c for c in roof_point(th, t))))
    print("lowest", lowest_y())
