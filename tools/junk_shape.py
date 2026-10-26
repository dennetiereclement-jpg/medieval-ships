"""Shape and layout of the Dragon Junk (dragon_junk), shared by the model generator, the interior grid, the
texture (the flattened sail panels) and the furniture.

MUST stay identical to fr.medievalships.core.JunkLayout (Java), which uses the same formulas and numbers for
the terrain probes, the seats and the autopilot (checked by JunkTest.matchesModelGenerator;
`python3 tools/junk_shape.py` prints the reference values).

Ship-local coordinates, in blocks: x = lateral (+x = port / babord), y = up (0 = the main deck), z = forward
(+z = bow). Measured on the reference sheet (side view: 0.1 block per pixel of the 1536 x 1024 sheet, see
docs/JUNK_PLAN.md): a long dark hull of 39 blocks from the square bow to the transom (42 with the beak, 46 with
the bowsprit), 8.8 wide, a beak (cutwater) pointing forwards low down under the square bow, the main deck open
from the bow to the break, a quarterdeck 2.5 blocks higher aft with the multi-level stern house (white plaster
walls, dark beams, a tall red roof of four stacked tiers with upturned edges), the companion house on the port
side at the break, one big mast stepped far forward and raked aft, carrying the great red sail with the black
dragon: two battened panels hanging from a short yard under the masthead, spread in a V (top view) like a tent
(front view), their clews held out by long pale booms.
"""
import math

CELL = 0.5
SLAB = 0.5          # every deck and floor is one cell thick
SHELL = 0.45        # hull planking (interior grid: the outermost cell)

# ---------------------------------------------------------------- levels
MAIN_DECK_Y = 0.0           # open main deck, from the break to the bow
QUARTERDECK_Y = 2.5         # aft of the break: the quarterdeck, the stern house stands on it
LOWER_DECK_Y = -3.0         # storage (forward) and main room (amidships), under the main deck
BEDROOM_Y = -0.5            # the bedroom under the quarterdeck (a step down from the main deck)
HOUSE_CEIL_Y = 6.0          # ceiling of the stern cabin (the roof above it)
RAIL_H = 1.0                # balustrades above the open decks

# ---------------------------------------------------------------- hull
BOW_Z = 19.5                # the square bow face (bulwark), the front of the main deck at 19.0
STERN_Z = -19.5             # the transom
HULL_HW = 4.4               # half beam amidships
BOW_HW = 3.5                # half width of the square bow face
STERN_HW = 3.8              # half width of the transom at the deck
FULL_Z = (-9.0, 9.5)        # full beam between these
BOW_PLAN_POW = 2.2
STERN_PLAN_POW = 2.0
SIDE_Y = -1.0               # the bilge turns into the straight sides here
FLAT = 0.24                 # half width of the flat of the bottom (fraction of the beam)
BILGE_POW = 3.2
SHEER_FORE = 1.0            # top of the white bulwark of the main deck
BREAK_Z = -1.5              # the break: the quarterdeck from here aft
BREAK_RISE = (1.2, -1.5)    # the white band rises from SHEER_FORE at z 1.2 to QUARTERDECK_Y at z -1.5
WALE_Y = -1.5               # the dark wale under the white band (the top of the beak at the bow face)
RED_BAND = (-1.05, 1.2)     # aft: the red lacquered panels between dark posts on the hull side
# the beak: a wedge of pale planks pointing forwards under the square bow, its top sloping down from the wale
BEAK_TIP_Z = 22.6
BEAK_TIP_Y = -3.6
PINCH_Z = 12.5              # forward of this the lower hull narrows into the beak
RUN = (-10.5, 9.0, 0.75, 1.3)   # aft of RUN[0], over RUN[1] blocks: the flat of the bottom shrinks by RUN[2], the bilge
#                                 exponent drops by RUN[3] (a V-shaped run up to the transom, as on the back view)
# the keel line (z, y): flat under the rooms, the stern rising in a long curve (the counter under the stern
# house), the beak's lower edge rising a little to its tip; monotone cubic through these
KEEL_PTS = ((-19.5, -1.9), (-18.5, -2.5), (-17.0, -3.2), (-15.0, -3.8), (-13.0, -4.25), (-11.0, -4.45), (-8.0, -4.5),
            (0.0, -4.5), (10.0, -4.5), (16.0, -4.4), (20.0, -4.15), (22.6, -3.6))

# ---------------------------------------------------------------- stern house (on the quarterdeck) and roof
HOUSE_FRONT_Z = -8.0        # outer face of its front wall (the door in it)
EAVE_Y = 5.0                # lowest edge of the roof (its four tiers rise to the ridge)
RIDGE_Y = 10.5
ROOF_HW = 5.4               # half width at the eaves (the roof overhangs the hull)
ROOF_FRONT_Z = -5.8         # the front gable overhangs the porch (at the eaves; it leans forwards up to the ridge)
GABLE_LEAN = 0.18           # the gable's edge comes forwards by this much a block of distance from the eaves
ROOF_BACK_Z = -20.4         # the hipped back overhangs the transom
ROOF_TIERS = 4
ROOF_CURVE = (0.35, 1.8)    # concave profile (see roof_y): flatter at the eaves, steep up to the ridge
STERN_POLE = ((0.0, 10.4, -14.0), (0.0, 13.6, -17.6))   # the short staff on the ridge, raked aft
# the companion house on the port side of the break (stairs down to the main room inside)
MID_X = (0.5, None)         # from x 0.5 to the hull side
MID_Z = (-1.5, 4.0)         # its walls (aft, fore)
MID_WALL_Y = 3.0            # eaves of its gable roof
MID_RIDGE_Y = 6.8
MID_ROOF_Z = (-1.9, 4.7)    # the roof overhangs fore and aft

# ---------------------------------------------------------------- mast, sail, spars
MAST_FOOT = (0.0, 0.0, 16.5)
MAST_RAKE_DEG = 26.0        # raked aft
MAST_HEAD_Y = 22.0
MAST_D = (0.72, 0.46)       # diameter at the deck, at the head
YARD = ((0.0, 16.0, 11.4), (0.0, 16.0, 6.6))   # the short head yard of the sail (fore end, aft end)
# the two sail panels (port +1, starboard -1): head on the yard, luff down to the tack near the centre line
# forward, leech down to the clew spread out aft (a V in plan, a tent from ahead)
SAIL_TACK = (0.45, 3.3, 20.2)
SAIL_CLEW = (7.0, 1.2, 3.0)
SAIL_BILLOW = 0.85
SAIL_BATTENS = (0.2, 0.37, 0.53, 0.68, 0.82)   # battens across the panels (s, from the head down)
FORE_BOOM = ((0.0, 3.35, 12.2), (0.0, 3.55, 21.1))  # the spar along the foot forward (the tacks lashed to its end)
CLEW_BOOM_END = (4.75, -1.25, -5.0)   # the long pale booms from the clews aft and down along the sides (x for port)
BOWSPRIT = ((0.0, 0.75, 18.6), (0.0, 0.15, 26.3))
BOW_YARD = ((0.0, 1.55, 19.2), (0.0, 1.05, 24.4))   # the small white bow sail hangs from it
BOW_SAIL_DROP = 3.3

# ---------------------------------------------------------------- fittings
ANCHOR = (4.6, 7.3)         # x (port side), z of the anchor's chain on the hull side
ANCHOR_TOP_Y = -4.0         # the anchor's ring; its crown hangs down to ANCHOR_BOTTOM_Y
ANCHOR_BOTTOM_Y = -6.4
HELM_Z = -4.8
PILOT_Z = -5.6
RUDDER_Z = (-14.0, -18.9)   # stock (fore edge of the blade) to the trailing edge
# outside stair on the port side of the quarterdeck (decorative boarding steps down the hull side)
SIDE_STAIR = ((4.65, 2.3, -8.3), (4.65, -2.6, -4.6))


# ---------------------------------------------------------------- formulas
def _smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def _slopes(p):
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


KEEL_SLOPES = _slopes(KEEL_PTS)


def keel_y(z):
    """Bottom of the hull at z (the beak's lower edge forward of the bow)."""
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


def plan_hw(z):
    """Half width of the hull at the sheer (deck level) at z, between the transom and the square bow."""
    if z > BOW_Z or z < STERN_Z:
        return 0.0
    if z > FULL_Z[1]:
        t = (z - FULL_Z[1]) / (BOW_Z - FULL_Z[1])
        return HULL_HW - (HULL_HW - BOW_HW) * t ** BOW_PLAN_POW
    if z < FULL_Z[0]:
        t = (FULL_Z[0] - z) / (FULL_Z[0] - STERN_Z)
        return HULL_HW - (HULL_HW - STERN_HW) * t ** STERN_PLAN_POW
    return HULL_HW


def beak_top(z):
    """Top edge of the beak forward of the bow face (it slopes down from the wale to the tip)."""
    t = (z - BOW_Z) / (BEAK_TIP_Z - BOW_Z)
    return WALE_Y + (BEAK_TIP_Y - WALE_Y) * max(0.0, min(1.0, t))


def sheer_y(z):
    """Top of the hull's side planking: the white bulwark of the main deck, rising at the break to the
    quarterdeck (whose balustrade stands on it)."""
    a, b = BREAK_RISE
    return SHEER_FORE + (QUARTERDECK_Y - SHEER_FORE) * _smooth((a - z) / (a - b))


def deck_y(z):
    return QUARTERDECK_Y if z <= BREAK_Z else MAIN_DECK_Y


def hull_x(z, y):
    """Half width of the outside of the hull at (z, y): a flat bottom turning in a round bilge into straight
    sides; forward the lower hull narrows into the beak under the square bow; the beak alone beyond the bow."""
    k = keel_y(z)
    if y < k or z < STERN_Z or z > BEAK_TIP_Z:
        return 0.0
    if z > BOW_Z:
        if y > beak_top(z):
            return 0.0
        w = BOW_HW
    else:
        w = plan_hw(z)
    if w <= 0:
        return 0.0
    if y >= SIDE_Y:
        x = w
    else:
        eta = (y - k) / (SIDE_Y - k) if SIDE_Y > k else 1.0
        fr = _smooth((RUN[0] - z) / RUN[1])
        flat = FLAT * (1.0 - RUN[2] * fr)
        x = w * (flat + (1.0 - flat) * (1.0 - (1.0 - eta) ** (BILGE_POW - RUN[3] * fr)) ** 0.5)
    if z > PINCH_Z and y < WALE_Y + 0.1:
        pz = _smooth((z - PINCH_Z) / (BEAK_TIP_Z - PINCH_Z))
        gy = _smooth((WALE_Y + 0.1 - y) / 0.8)
        x *= 1.0 - 0.9 * pz * gy
    if z > BEAK_TIP_Z - 1.6:
        x *= (BEAK_TIP_Z - z) / 1.6
    return x


def inside_hull(x, y, z, inset=0.0):
    if y > sheer_y(z) or y < keel_y(z) + inset:
        return False
    return abs(x) <= hull_x(z, y) - inset


# ---------------------------------------------------------------- roof of the stern house
def roof_d(x, z):
    """Distance from the eave line of the roof (plan): the sides, the hipped back; the front is a gable."""
    return min(ROOF_HW - abs(x), z - ROOF_BACK_Z)


def roof_y(d):
    """Height of the roof surface at a distance d from its eaves: four tiers on a concave profile (steeper near
    the ridge), each tier's lower edge kicked up a little."""
    d = max(0.0, min(ROOF_HW, d))
    t = d / ROOF_HW
    a, p = ROOF_CURVE
    return EAVE_Y + (RIDGE_Y - EAVE_Y) * (a * t + (1.0 - a) * t ** p)


def roof_front_z(d):
    """z of the front gable's edge at a distance d from the eaves (the ridge juts forwards)."""
    return ROOF_FRONT_Z + GABLE_LEAN * max(0.0, d)


def roof_tiers():
    """(d0, d1) of each tier from the eaves up."""
    edges = [0.0, 1.5, 2.8, 3.95, ROOF_HW]
    return [(edges[i], edges[i + 1]) for i in range(ROOF_TIERS)]


# ---------------------------------------------------------------- mast and sail
def mast_dir():
    a = math.radians(MAST_RAKE_DEG)
    return (0.0, math.cos(a), -math.sin(a))


def mast_point(y):
    """Point of the mast's axis at height y."""
    d = mast_dir()
    t = (y - MAST_FOOT[1]) / d[1]
    return (0.0, y, MAST_FOOT[2] + d[2] * t)


def mast_head():
    return mast_point(MAST_HEAD_Y)


def sail_corners(side):
    """Head fore, head aft, tack, clew of the sail panel on this side (+1 port, -1 starboard)."""
    h0 = (side * 0.14, YARD[0][1] - 0.18, YARD[0][2] - 0.2)
    h1 = (side * 0.14, YARD[1][1] - 0.18, YARD[1][2] + 0.25)
    tack = (side * SAIL_TACK[0], SAIL_TACK[1], SAIL_TACK[2])
    clew = (side * SAIL_CLEW[0], SAIL_CLEW[1], SAIL_CLEW[2])
    return h0, h1, tack, clew


def _lerp(a, b, t):
    return tuple(p + (q - p) * t for p, q in zip(a, b))


def sail_flat(side, s, t):
    """Point of the panel without billow: s from the head (0) down to the foot (1), t from the luff (0) to the
    leech (1)."""
    h0, h1, tack, clew = sail_corners(side)
    return _lerp(_lerp(h0, h1, t), _lerp(tack, clew, t), s)


def sail_normal(side):
    """Outward normal of the panel (away from the centre line)."""
    h0, h1, tack, clew = sail_corners(side)
    a = [q - p for p, q in zip(h0, clew)]
    b = [q - p for p, q in zip(h1, tack)]
    n = (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])
    ln = math.sqrt(sum(c * c for c in n))
    n = tuple(c / ln for c in n)
    return n if n[0] * side > 0 else tuple(-c for c in n)


def sail_point(side, s, t, billow=1.0):
    """Point of the panel, billowed out by the wind (most in the middle, none on the yard)."""
    p = sail_flat(side, s, t)
    n = sail_normal(side)
    sc, tc = max(0.0, min(1.0, s)), max(0.0, min(1.0, t))
    b = SAIL_BILLOW * billow * math.sin(math.pi * sc) ** 0.9 * math.sin(math.pi * tc) ** 0.8
    return tuple(c + nc * b for c, nc in zip(p, n))


def clew_boom(side):
    c = sail_point(side, 1.0, 1.0)
    end = (side * CLEW_BOOM_END[0], CLEW_BOOM_END[1], CLEW_BOOM_END[2])
    return c, end


# ---------------------------------------------------------------- extents (Java: probes, autopilot)
def lowest_y():
    return ANCHOR_BOTTOM_Y - 0.05


def top_y():
    return MAST_HEAD_Y + 0.9


if __name__ == "__main__":
    print("keel", [round(keel_y(z), 6) for z in (-19.0, -14.0, -6.0, 15.0, 21.0)])
    print("plan", [round(plan_hw(z), 6) for z in (-18.0, -12.0, 0.0, 14.0, 19.0)])
    print("sheer", [round(sheer_y(z), 6) for z in (3.0, 0.5, -0.4, -1.2, -5.0)])
    for z, y in ((0.0, -3.5), (0.0, -2.0), (-16.0, -1.0), (15.0, -3.0), (18.5, -2.5), (20.5, -2.8), (19.0, 0.5), (-18.0, 1.5)):
        print("hull_x", z, y, round(hull_x(z, y), 6))
    print("mast head", [round(c, 6) for c in mast_head()])
    for side in (1, -1):
        print("sail", side, [round(c, 6) for c in sail_point(side, 0.5, 0.5)], [round(c, 6) for c in sail_point(side, 1.0, 1.0)])
    print("roof", [round(roof_y(d), 6) for d in (0.0, 1.55, 2.95, 4.25, 5.8)])
