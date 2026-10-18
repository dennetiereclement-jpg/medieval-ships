"""Shape and layout of the steampunk airship (steampunk_airship), shared by the model generator.

MUST stay identical to Ships.steampunkAirship() / AirshipLayout (Java), which use the same
formulas and numbers for collisions, seats, terrain probes and the autopilot (checked by
AirshipTest.matchesModelGenerator).

Ship-local coordinates, in blocks: x = lateral (+x = port), y = up (0 = gondola deck),
z = forward (+z = bow). The gondola is a small wooden hull; the balloon is a body of
revolution about the axis (y = BALLOON_Y, along z).
"""
import math

# ---- gondola (a small boat hull: same formulas as the ships)
HALF_LENGTH = 7.0
TIP = 7.6
MAX_HALF_WIDTH = 1.8
FORE_SCALE, FORE_POW_A, FORE_POW_B = 7.6, 2.0, 0.75
AFT_SCALE, AFT_POW_A, AFT_POW_B = 7.5, 2.4, 0.6
KEEL_DEPTH, KEEL_RISE, KEEL_POW = 1.4, 1.3, 2.0
# raised bow and stern
RAIL_BASE, RAIL_RISE_FORE, RAIL_RISE_AFT, RAIL_POW = 1.0, 1.7, 1.3, 2.2
BOTTOM_SECTION = [(0.0, 1.0), (0.5, 0.88), (0.85, 0.5), (0.98, 0.1)]
WATERLINE_Y = 0.0
MAIN_DECK_Y = 0.0
DECK_MIN_Z, DECK_MAX_Z = -6.4, 6.4
LOWEST_Y = -1.65          # under the keel feet

# ---- balloon: radius(z) = R * (1 - t^a)^b, t = |z - BALLOON_Z| / BALLOON_HALF (a, b fore / aft)
BALLOON_Z = -1.1
BALLOON_Y = 10.4
BALLOON_HALF = 9.5
BALLOON_R = 4.25
BALLOON_FORE = (2.4, 0.5)
BALLOON_AFT = (2.0, 0.55)
BALLOON_FRONT_Z = BALLOON_Z + BALLOON_HALF          # 8.4
BALLOON_REAR_T = 0.92                               # the cloth ends here; the tail cone takes over
BALLOON_REAR_Z = BALLOON_Z - BALLOON_HALF * BALLOON_REAR_T
NOSE_ROD_Z = BALLOON_FRONT_Z + 2.0
# tail: lattice cone from the balloon to the propeller shaft
TAIL_END_Z = -14.6
PROP_Z = -15.2
PROP_R = 2.4
PROP_BLADES = 6
# fins: azimuth from the top (degrees, + to port), root along the balloon, tip beyond it
FIN_AZIMUTHS = (0.0, 125.0, -125.0)
FIN_ROOT_Z = (-3.6, -9.6)
FIN_TIP_Z = -12.4
FIN_SPAN = 5.0

# ---- gondola fittings
PILLAR_Z = BALLOON_Z
HELM_Z = -3.6
PILOT_Z = -4.5
ENGINE_Z = (-6.6, -5.0)
BENCH_Z = (1.0, 3.2)
BOW_SEAT_Z = 5.6


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


def balloon_radius(z):
    t = (z - BALLOON_Z) / BALLOON_HALF
    a, b = BALLOON_FORE if t >= 0 else BALLOON_AFT
    t = abs(t)
    if t >= 1.0:
        return 0.0
    return BALLOON_R * (1.0 - t ** a) ** b


def balloon_point(z, azimuth, out=0.0):
    """Point of the balloon surface at z, azimuth (radians from the top, + towards port)."""
    r = balloon_radius(z) + out
    return (math.sin(azimuth) * r, BALLOON_Y + math.cos(azimuth) * r, z)


if __name__ == "__main__":
    for z in (-6.0, -2.0, 0.0, 3.0, 6.0):
        print("{%s, %.6f, %.6f, %.6f}," % (z, half_width(z), rail_y(z), keel_y(z)))
    for z in (-9.0, -5.0, -1.1, 3.0, 7.5):
        print("{%s, %.6f}," % (z, balloon_radius(z)))
