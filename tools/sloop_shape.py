"""Hull shape and layout of the trade sloop (trade_sloop), shared by the model generator.

MUST stay identical to fr.medievalships.core.HullShape + SloopLayout.type() (Java), which use
the same formulas and numbers for collisions, seats and terrain probes (checked by
SloopTest.matchesModelGenerator).

Ship-local coordinates, in blocks:
  x = lateral (+x = port / babord), y = up (0 = model origin, the water is at WATERLINE_Y),
  z = forward (+z = bow).

Reference: a small, chunky merchant sloop. Brown planking with a wide band of blue strakes along
the sides, crossed by brown frames; a raised bow with a long bowsprit; one mast with a big gaff
mainsail and a large jib; a small raised stern platform with the cargo and the tiller.
"""

HALF_LENGTH = 7.5
TIP = 8.2
MAX_HALF_WIDTH = 2.3
# full, rounded entry; a rounder, fuller run aft (the stern is almost round in plan)
FORE_SCALE, FORE_POW_A, FORE_POW_B = 8.1, 2.0, 0.8
AFT_SCALE, AFT_POW_A, AFT_POW_B = 8.0, 3.2, 0.6
KEEL_DEPTH, KEEL_RISE, KEEL_POW = 1.5, 1.1, 2.6
# strong sheer at the bow (raised stem), a little at the stern
RAIL_BASE, RAIL_RISE_FORE, RAIL_RISE_AFT, RAIL_POW = 2.1, 1.4, 0.25, 2.2
# the bulwark is at least this high above the decks (the stern platform keeps a low rail)
RAIL_ABOVE_DECK = 0.95
BOTTOM_SECTION = [(0.0, 1.0), (0.45, 0.9), (0.8, 0.55), (0.97, 0.15)]
WATERLINE_Y = -0.5

MAIN_DECK_Y = 0.6
# small raised stern platform (storage and the tiller), one step up from the main deck
AFT_DECK_Y = 1.1
AFT_DECK_START = -3.6
DECK_MIN_Z, DECK_MAX_Z = -6.9, 6.9
MAST_Z = 1.2
MAST_TOP = 14.0
CROSSTREE_Y = 11.0
# tiller (the pilot stands at it, on the stern platform)
PILOT_Z = -5.0
HELM_Z = -6.0
RUDDER_Z = -7.7
# spars: boom, gaff (throat on the mast, peak aft and up), bowsprit (heel on the stem head)
BOOM_Y, BOOM_END_Z = 3.1, -8.8
GAFF_THROAT_Y, GAFF_PEAK = 10.2, (11.6, -6.3)   # throat height; (y, z) of the peak
BOWSPRIT_HEEL = (3.45, 6.9)                     # (y, z)
BOWSPRIT_TIP = (4.9, 12.2)
# jib: head high on the mast, tack at the bowsprit end, clew near the mast foot
JIB_HEAD_Y, JIB_CLEW = 10.6, (3.2, 2.2)         # (y, z)
# passenger seats (x, z): two benches along the bulwarks amidships, a bench at the bow; a crate to sit on at the stern
BENCH_SEATS = [(1.55, -2.0), (-1.55, -2.0), (0.0, 4.8)]
AFT_SEAT = (1.0, -6.3)
# cargo (solid boxes the player bumps into and can stand on): crates (x, z, size) and barrels (x, z, r)
CRATES = [(-0.85, -6.3, 0.72), (-0.85, -5.45, 0.6), (1.0, -6.3, 0.7), (1.3, 3.6, 0.62), (1.3, 2.95, 0.5)]
BARRELS = [(1.5, 0.3, 0.3), (-1.55, 0.3, 0.3), (-1.2, 4.1, 0.28)]


def half_width(z):
    fore = z >= 0
    a = abs(z) / (FORE_SCALE if fore else AFT_SCALE)
    if a >= 1.0:
        return 0.0
    pa, pb = (FORE_POW_A, FORE_POW_B) if fore else (AFT_POW_A, AFT_POW_B)
    return MAX_HALF_WIDTH * (1.0 - a ** pa) ** pb


def deck_y(z):
    return AFT_DECK_Y if z < AFT_DECK_START else MAIN_DECK_Y


def sheer_y(z):
    a = abs(z) / HALF_LENGTH
    rise = RAIL_RISE_FORE if z >= 0 else RAIL_RISE_AFT
    return RAIL_BASE + rise * a ** RAIL_POW


def rail_y(z):
    return max(sheer_y(z), deck_y(z) + RAIL_ABOVE_DECK)


def keel_y(z):
    a = abs(z) / HALF_LENGTH
    return -KEEL_DEPTH + KEEL_RISE * a ** KEEL_POW


def inner_half_width(z):
    return max(0.0, 0.97 * half_width(z) - 0.12)


def bottom_y(z, ax):
    w, yk = half_width(z), keel_y(z)
    if w <= 0.1:
        return yk
    s = BOTTOM_SECTION
    if ax >= s[-1][0] * w:
        return s[-1][1] * yk
    for i in range(len(s) - 1):
        x0, x1 = s[i][0] * w, s[i + 1][0] * w
        if ax <= x1:
            f = (ax - x0) / (x1 - x0)
            return s[i][1] * yk + (s[i + 1][1] - s[i][1]) * yk * f
    return s[-1][1] * yk


if __name__ == "__main__":
    for z in (-7.0, -5.0, -3.0, 0.0, 3.0, 6.0, 7.0):
        print("{%s, %.6f, %.6f, %.6f, %.6f, %.6f}," % (z, half_width(z), rail_y(z), keel_y(z), bottom_y(z, 1.2), deck_y(z)))
