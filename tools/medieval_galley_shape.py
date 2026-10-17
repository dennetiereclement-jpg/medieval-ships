"""Hull shape and layout of the red medieval galley (medieval_galley), shared by the model generator.

MUST stay identical to fr.medievalships.core.HullShape + Ships.medievalGalley() (Java), which
use the same formulas and numbers for collisions, seats and terrain probes (checked by
MedievalGalleyTest.hullMatchesModelGenerator).

Ship-local coordinates, in blocks:
  x = lateral (+x = port / babord), y = up (0 = model origin, the water is at WATERLINE_Y),
  z = forward (+z = bow).
"""

HALF_LENGTH = 12.6
TIP = 13.6
MAX_HALF_WIDTH = 2.5
FORE_SCALE, FORE_POW_A, FORE_POW_B = 13.2, 2.1, 0.75
AFT_SCALE, AFT_POW_A, AFT_POW_B = 13.2, 2.1, 0.75
KEEL_DEPTH, KEEL_RISE, KEEL_POW = 1.25, 1.2, 3.0
# crescent sheer: low amidships, sweeping up to the dragon necks at both ends
RAIL_BASE, RAIL_RISE_FORE, RAIL_RISE_AFT, RAIL_POW = 1.75, 2.2, 2.2, 3.0
BOTTOM_SECTION = [(0.0, 1.0), (0.5, 0.88), (0.85, 0.5), (0.98, 0.1)]
WATERLINE_Y = -0.45

MAIN_DECK_Y = 0.45
DECK_MIN_Z, DECK_MAX_Z = -11.2, 11.2
MAST_Z, MAST_TOP = 0.6, 13.2
YARD_Y, YARD_HALF = 12.0, 5.4
PILOT_Z = -10.2
STEER_Z = -10.9
# rowing benches (two seats each) and the oars: 12 per side, one bench every two oars
BENCH_Z = [-7.6, -4.4, 3.6, 6.8]
OAR_Z = [-8.8 + 1.6 * k for k in range(12)]
SHIELD_Z = [-8.775 + 1.35 * k for k in range(14)]


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
    for z in (-12.0, -8.0, 0.0, 6.0, 12.0):
        print("{%s, %.6f, %.6f, %.6f, %.6f}," % (z, half_width(z), rail_y(z), keel_y(z), bottom_y(z, 1.2)))
