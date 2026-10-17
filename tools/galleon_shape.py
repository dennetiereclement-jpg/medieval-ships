"""Hull shape and layout of the great galleon, shared by the model generator.

MUST stay identical to fr.medievalships.core.HullShape + Ships.galleon() (Java),
which use the same formulas and numbers for collisions, seats and terrain probes
(checked by GalleonTest.hullMatchesModelGenerator).

Ship-local coordinates, in blocks:
  x = lateral (+x = port / babord), y = up (0 = model origin, the water is at WATERLINE_Y), z = forward (+z = bow).
"""

HALF_LENGTH = 17.5
TIP = 18.3
MAX_HALF_WIDTH = 4.5
FORE_SCALE, FORE_POW_A, FORE_POW_B = 18.0, 2.0, 0.6
AFT_SCALE, AFT_POW_A, AFT_POW_B = 19.5, 3.0, 0.5
KEEL_DEPTH, KEEL_RISE, KEEL_POW = 2.9, 2.1, 3.0
WATERLINE_Y = -1.5  # water surface under the model origin when afloat (the hull floats high)
RAIL_BASE, RAIL_RISE_FORE, RAIL_RISE_AFT, RAIL_POW = 2.2, 0.8, 0.8, 2.5
BOTTOM_SECTION = [(0.0, 1.0), (0.45, 0.92), (0.8, 0.6), (0.97, 0.15)]

MAIN_DECK_Y = 1.0
FORECASTLE_Y = 3.0
FORECASTLE_START = 10.5
QUARTERDECK_Y = 3.6
QUARTERDECK_SLAB = 0.3
BULKHEAD_Z = -8.5
BULKHEAD_THICK = 0.3
DOOR_HALF = 0.7
DOOR_TOP = 3.05
TRANSOM_Z = -17.3
DECK_MAX_Z = 17.2
POOP_FRONT = -14.2
POOP_BACK = -16.9
POOP_HALF = 2.9
POOP_WALL_TOP = 6.3
POOP_RIDGE = 7.4
MAIN_MAST_Z, MAIN_MAST_TOP = 1.5, 25.5
FORE_MAST_Z, FORE_MAST_TOP = 12.8, 21.0
MIZZEN_Z, MIZZEN_TOP = -12.6, 17.5
HELM_Z = -9.6
PILOT_Z = -10.35
STAIR_X0, STAIR_X1 = 1.9, 3.6
FC_STAIR_X0, FC_STAIR_X1 = 1.5, 3.0
QD_STAIR_START = -6.0
FC_STAIR_START = 8.5
STEP_DEPTH = 0.5
RAIL_HEIGHT = 0.9
RAIL_THICK = 0.12
BALCONY_BACK = -18.3
BALCONY_HALF = 2.3
BALCONY_FLOOR = 0.25
BALCONY_RAIL = 1.0
GUNPORT_Z = [-6.0, -3.0, 0.0, 2.75, 5.5, 8.0]
GUNPORT_Y = 1.62
BENCH_Z = [-4.5, -1.5, 4.0, 7.0]
QD_RAIL_Y = QUARTERDECK_Y + 1.0   # castle bulwarks (rail floors)
FC_RAIL_Y = FORECASTLE_Y + 1.0


def half_width(z):
    fore = z >= 0
    a = abs(z) / (FORE_SCALE if fore else AFT_SCALE)
    if a >= 1.0:
        return 0.0
    pa, pb = (FORE_POW_A, FORE_POW_B) if fore else (AFT_POW_A, AFT_POW_B)
    return MAX_HALF_WIDTH * (1.0 - a ** pa) ** pb


def deck_y(z):
    return FORECASTLE_Y if z > FORECASTLE_START else MAIN_DECK_Y


def sheer_y(z):
    """Rail of the hull itself (without the castle bulwarks)."""
    a = abs(z) / HALF_LENGTH
    rise = RAIL_RISE_FORE if z >= 0 else RAIL_RISE_AFT
    return RAIL_BASE + rise * a ** RAIL_POW


def rail_y(z):
    y = sheer_y(z)
    if z < BULKHEAD_Z:
        y = max(y, QD_RAIL_Y)
    if z > FORECASTLE_START:
        y = max(y, FC_RAIL_Y)
    return y


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
    for z in (-17.3, -12.0, 0.0, 9.0, 15.5):
        print(z, round(half_width(z), 6), round(rail_y(z), 6), round(keel_y(z), 6), round(bottom_y(z, 2.0), 6))
