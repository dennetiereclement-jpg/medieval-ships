"""Shape and layout of the steampunk hot-air balloon (hot_air_balloon), shared by the model generator and
the texture.

MUST stay identical to BalloonLayout (Java), which uses the same formulas and numbers for the collisions,
the seats, the terrain probes and the autopilot (checked by BalloonTest.matchesModelGenerator).

Ship-local coordinates, in blocks: x = lateral (+x = port), y = up (0 = the basket's deck), z = forward
(+z = bow). The basket is a small boat hull (same formulas as the other hulls); the envelope is a body of
revolution about the vertical axis x = z = 0, its radius given by balloon_radius(y) between the mouth
(MOUTH_Y) and the crown (TOP_Y).
"""
import math

# ---- the basket: a small boat hull with raised ends
HALF_LENGTH = 4.6
TIP = 5.1
MAX_HALF_WIDTH = 1.85
FORE_SCALE, FORE_POW_A, FORE_POW_B = 5.15, 2.6, 0.7
AFT_SCALE, AFT_POW_A, AFT_POW_B = 5.15, 2.6, 0.7
KEEL_DEPTH, KEEL_RISE, KEEL_POW = 1.3, 0.95, 2.0
RAIL_BASE, RAIL_RISE_FORE, RAIL_RISE_AFT, RAIL_POW = 1.0, 0.38, 0.38, 2.2
BOTTOM_SECTION = [(0.0, 1.0), (0.55, 0.9), (0.88, 0.55), (0.99, 0.12)]
WATERLINE_Y = 0.0
MAIN_DECK_Y = 0.0
DECK_MIN_Z, DECK_MAX_Z = -4.2, 4.2
# the lanterns hang under the ends of the hull: the lowest point of the vehicle
LANTERN_Z = 3.7
LANTERN_DROP = 1.3           # the lanterns' chains, from the hooks under the rail
LOWEST_Y = -1.5              # the keel bar under the middle of the hull

# ---- the envelope: radius(y) = R * profile(f), f = (y - MOUTH_Y) / (TOP_Y - MOUTH_Y), Catmull-Rom through PROFILE
R = 6.7
MOUTH_Y = 5.0
TOP_Y = 19.4
# (f, r / R): the mouth, the skirt widening like a cone, a full round belly, the broad crown closing over the top
PROFILE = [(0.0, 0.35), (0.08, 0.5), (0.2, 0.68), (0.32, 0.84), (0.45, 0.95), (0.56, 1.0), (0.66, 0.99),
           (0.77, 0.93), (0.87, 0.8), (0.94, 0.6), (0.98, 0.32), (1.0, 0.0)]
CROWN_F = 0.975              # the cloth ends here; a brass crown plate closes the top
BAND_F = 0.4                 # the brass load band with its ornaments and the chains' shackles
GORES = 20                   # gores, olive green and beige alternately

# ---- suspension: 8 chains from the band to the basket's rail; 8 ropes from the band down to the mouth collar
CHAIN_AZIMUTHS = (22.5, 67.5, 112.5, 157.5, 202.5, 247.5, 292.5, 337.5)   # degrees from the bow, + to port
# (x, z) on the rail where each chain is made fast (same order)
CHAIN_RAIL = [(0.6, 4.4), (1.65, 2.4), (1.75, -0.7), (1.0, -3.8), (-1.0, -3.8), (-1.75, -0.7), (-1.65, 2.4), (-0.6, 4.4)]
MOUTH_R = R * 0.35           # the brass collar at the mouth

# ---- the burner column, the platform, the machinery
COLUMN_Z = 0.0
PLATFORM_Y = 2.5             # the small square platform half way up the column
PLATFORM_HALF = 0.85
BURNER_Y = 4.05              # the burner head (its flame rises into the mouth)
FLAME_TOP = 5.9
BOILER_Z = -2.4              # the black iron boiler and its stack, aft of the column
BOILER_X = 0.45
STACK_TOP = 3.9
WHEEL_Z = -2.4               # the big wooden gear wheel on the side of the stern
WHEEL_R = 1.4
WHEEL_Y = 2.3
WHEEL_SIDE = 1               # on the port side (+x), as on the picture
WHEEL_X = WHEEL_SIDE * (MAX_HALF_WIDTH + 0.42)   # its plane, outside the hull
HELM_Z = -1.3                # the brass control stand (the valve wheel) on the column, facing aft
PILOT_Z = -2.1               # the pilot stands here, facing the bow
BENCH_Z = 1.9                # the two side benches, facing inwards
BOW_SEAT_Z = 3.5             # the bow bench, facing aft


def _cr(p0, p1, p2, p3, t):
    return 0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3)


def profile(f):
    """r / R of the envelope at the height fraction f (0 = mouth, 1 = crown): Catmull-Rom through PROFILE."""
    if f <= 0.0:
        return PROFILE[0][1]
    if f >= 1.0:
        return 0.0
    n = len(PROFILE)
    i = 0
    while i < n - 2 and f >= PROFILE[i + 1][0]:
        i += 1
    f0, r0 = PROFILE[i]
    f1, r1 = PROFILE[i + 1]
    t = (f - f0) / (f1 - f0)
    rm = PROFILE[max(0, i - 1)][1]
    rp = PROFILE[min(n - 1, i + 2)][1]
    return max(0.0, _cr(rm, r0, r1, rp, t))


def balloon_radius(y):
    return R * profile((y - MOUTH_Y) / (TOP_Y - MOUTH_Y))


def fy(f):
    """Height of the height fraction f."""
    return MOUTH_Y + (TOP_Y - MOUTH_Y) * f


def balloon_point(f, azimuth, out=0.0):
    """Point of the envelope at the height fraction f and the azimuth (radians from the bow, + towards port)."""
    r = R * profile(f) + out
    return (math.sin(azimuth) * r, fy(f), math.cos(azimuth) * r)


# ---- the basket hull (same formulas as HullShape)
def half_width(z):
    fore = z >= 0
    a = abs(z) / (FORE_SCALE if fore else AFT_SCALE)
    if a >= 1.0:
        return 0.0
    pa, pb = (FORE_POW_A, FORE_POW_B) if fore else (AFT_POW_A, AFT_POW_B)
    return MAX_HALF_WIDTH * (1.0 - a ** pa) ** pb


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


if __name__ == "__main__":
    for z in (-3.5, -2.0, 0.0, 2.0, 3.5):
        print("{%s, %.6f, %.6f, %.6f}," % (z, half_width(z), rail_y(z), keel_y(z)))
    for y in (5.0, 7.0, 10.0, 13.0, 16.0, 18.5, 19.3):
        print("{%s, %.6f}," % (y, balloon_radius(y)))
