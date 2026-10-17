"""Hull shape and layout of the armoured steam paddleboat (steam_paddleboat), shared by the model generator.

MUST stay identical to fr.medievalships.core.HullShape + Ships.steamPaddleboat() (Java), which
use the same formulas and numbers for collisions, seats and terrain probes (checked by
NewShipsTest.paddleboatMatchesModelGenerator).

Ship-local coordinates, in blocks:
  x = lateral (+x = port / babord), y = up (0 = model origin, the water is at WATERLINE_Y),
  z = forward (+z = bow).
"""

HALF_LENGTH = 10.5
TIP = 11.2
MAX_HALF_WIDTH = 4.0
# pointed bow, round stern
FORE_SCALE, FORE_POW_A, FORE_POW_B = 11.2, 2.0, 0.7
AFT_SCALE, AFT_POW_A, AFT_POW_B = 11.6, 3.2, 0.42
KEEL_DEPTH, KEEL_RISE, KEEL_POW = 1.8, 0.7, 4.0
# almost flat sheer; the rail is the iron railing round the deck
RAIL_BASE, RAIL_RISE_FORE, RAIL_RISE_AFT, RAIL_POW = 3.3, 0.35, 0.2, 2.0
BOTTOM_SECTION = [(0.0, 1.0), (0.6, 0.94), (0.9, 0.62), (0.99, 0.18)]
WATERLINE_Y = -0.8

MAIN_DECK_Y = 2.4
PLATING_TOP = 2.55        # top of the armour plating (the railing stands above it)
DECK_MIN_Z, DECK_MAX_Z = -10.3, 10.3

# deckhouse amidships (closed, the funnels on its roof)
HOUSE_Z0, HOUSE_Z1 = -5.0, 4.0
HOUSE_HALF = 2.5
HOUSE_TOP = 4.7
FUNNEL_Z = [-1.9, 1.3]
FUNNEL_HALF = 0.55
FUNNEL_TOP = 10.9
# helm in front of the deckhouse
HELM_Z = 5.75
PILOT_Z = 5.0
# side paddle wheel on the starboard side (-x), axle across, partly under water
WHEEL_Z = 1.2
WHEEL_Y = 0.75
WHEEL_R = 2.45
WHEEL_X0, WHEEL_X1 = 4.2, 5.7      # inner and outer faces of the wheel (|x|)
BOX_X1 = 6.0                       # outer face of the paddle box
# guns on turntables, fore and aft
GUN_FORE_Z = 8.0
GUN_AFT_Z = -7.6
MAST_Z, MAST_TOP = -9.0, 9.6


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
    for z in (-10.0, -6.0, 0.0, 5.0, 10.0):
        print("{%s, %.6f, %.6f, %.6f, %.6f}," % (z, half_width(z), rail_y(z), keel_y(z), bottom_y(z, 2.0)))
