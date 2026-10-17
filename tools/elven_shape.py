"""Hull shape and layout of the elven sailboat (elven_sailboat), shared by the model generator.

MUST stay identical to fr.medievalships.core.HullShape + Ships.elvenSailboat() (Java), which
use the same formulas and numbers for collisions, seats and terrain probes (checked by
NewShipsTest.elvenMatchesModelGenerator).

Ship-local coordinates, in blocks:
  x = lateral (+x = port / babord), y = up (0 = model origin, the water is at WATERLINE_Y),
  z = forward (+z = bow).
"""

HALF_LENGTH = 12.0
TIP = 13.0
MAX_HALF_WIDTH = 3.0
# fine entry, slender run aft
FORE_SCALE, FORE_POW_A, FORE_POW_B = 13.0, 1.8, 0.9
AFT_SCALE, AFT_POW_A, AFT_POW_B = 12.8, 2.2, 0.7
KEEL_DEPTH, KEEL_RISE, KEEL_POW = 1.9, 1.3, 2.5
# long elegant sheer, rising at the bow more than at the stern
RAIL_BASE, RAIL_RISE_FORE, RAIL_RISE_AFT, RAIL_POW = 1.85, 1.6, 1.2, 2.5
BOTTOM_SECTION = [(0.0, 1.0), (0.4, 0.9), (0.78, 0.55), (0.97, 0.12)]
WATERLINE_Y = -0.6

MAIN_DECK_Y = 0.6
DECK_MIN_Z, DECK_MAX_Z = -11.0, 11.0
MAST_Z, MAST_TOP = 1.0, 19.2
HELM_Z = -9.4
PILOT_Z = -10.2
BOOM_Y, BOOM_END_Z = 2.7, -10.4
# carved prow and stern ends (decoration beyond the hull, no collision)
PROW_TIP = (4.7, 16.7)     # (y, z) of the prow scroll
STERN_TIP = (4.6, -14.3)


def half_width(z):
    fore = z >= 0
    a = abs(z) / (FORE_SCALE if fore else AFT_SCALE)
    if a >= 1.0:
        return 0.0
    pa, pb = (FORE_POW_A, FORE_POW_B) if fore else (AFT_POW_A, AFT_POW_B)
    return MAX_HALF_WIDTH * (1.0 - a ** pa) ** pb


def deck_y(z):
    return MAIN_DECK_Y


def sheer_y(z):
    a = abs(z) / HALF_LENGTH
    rise = RAIL_RISE_FORE if z >= 0 else RAIL_RISE_AFT
    return RAIL_BASE + rise * a ** RAIL_POW


def rail_y(z):
    return sheer_y(z)


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
    for z in (-11.0, -6.0, 0.0, 6.0, 11.0):
        print("{%s, %.6f, %.6f, %.6f, %.6f}," % (z, half_width(z), rail_y(z), keel_y(z), bottom_y(z, 1.5)))
