"""Shape and layout of the Rowboat (rowboat), shared by the model generator and the texture.

MUST stay identical to fr.medievalships.core.RowboatLayout (Java), which gives the same numbers to HullShape
(collisions, seats, terrain probes, autopilot; checked by RowboatTest.matchesModelGenerator).

Ship-local coordinates, in blocks: x = lateral (+x = port), y = up (0 = the water surface), z = forward
(+z = bow). Measured on the reference (docs/ROWBOAT_PLAN.md): a 5 block hull (5.45 post to post), 2 wide,
freeboard 0.78 amidships rising to the two pointed ends, 0.32 of draught, three thwarts just under the
gunwale and a small triangular seat board at the stern.
"""
import math

# ---------------------------------------------------------------- hull (HullShape.Params in Java)
HALF_LENGTH = 2.5          # the planking ends here
TIP = 2.72                 # outer faces of the stem and stern posts
MAX_HW = 1.0               # half beam
# plan: hw = MAX_HW (1 - (|z| / scale) ^ a) ^ b, fore and aft (the stern a little fuller)
FORE_PLAN = (2.62, 2.3, 0.56)
AFT_PLAN = (2.62, 2.3, 0.6)
# keel: y = -depth + rise (|z| / HALF_LENGTH) ^ pow (rocker)
KEEL = (0.32, 0.24, 2.2)
# sheer: y = base + rise (|z| / HALF_LENGTH) ^ pow, rise fore / aft
RAIL = (0.78, 0.33, 0.26, 2.6)
WATERLINE_Y = 0.0
FLOOR_Y = -0.12            # top of the floorboards (the "deck" of HullShape): keel + 0.2 amidships
DECK_Z = (-2.1, 2.1)
# bottom cross-section (x / hw, y / keelY) from the keel outwards, as HullShape.bottomY
BOTTOM_SECTION = ((0.0, 1.0), (0.45, 0.9), (0.8, 0.55), (0.97, 0.15))

# ---------------------------------------------------------------- fittings
THWART_Z = (1.25, 0.05, -1.15)   # fore, middle (the rower), aft (the passenger)
THWART_TOP = 0.62
THWART_W = 0.5
THWART_TH = 0.08
STERN_SEAT_Z = (-2.45, -2.0)     # the small triangular board at the stern
OARLOCK_Z = 0.35                 # the rower's tholepins (just forward of the middle thwart)
FORE_LOCK_Z = 1.55               # the second pair of tholepins (forward position, no oars)
PIN_GAP = 0.16                   # half distance between the two pins of a pair
PILOT_Z = THWART_Z[1]
PASSENGER_Z = THWART_Z[2]
SEAT_Y = THWART_TOP
# the oars: the pivot on the gunwale, the shaft sloping down outboard
OAR_IN = 1.1                     # handle end to the tholepin
OAR_OUT = 2.45                   # tholepin to the blade's tip
OAR_BLADE = 0.85
OAR_BLADE_W = 0.24
OAR_DOWN_DEG = 18.0
OAR_TH = 0.09
RIB_Z = (-2.0, -1.55, -1.1, -0.65, -0.2, 0.25, 0.7, 1.15, 1.6, 2.0)
GUNWALE_W = 0.28
GUNWALE_H = 0.14
BAND_Z = (-1.9, -1.0, 0.0, 1.0, 1.9)   # the iron bands round the gunwale
POST_W = 0.18
POST_TOP = 0.2                   # the posts stick out this far above the rail's end


def _plan(z):
    scale, a, b = FORE_PLAN if z >= 0 else AFT_PLAN
    t = abs(z) / scale
    if t >= 1.0:
        return 0.0
    return MAX_HW * (1.0 - t ** a) ** b


def half_width(z):
    return _plan(z)


def keel_y(z):
    depth, rise, p = KEEL
    return -depth + rise * (abs(z) / HALF_LENGTH) ** p


def rail_y(z):
    base, rf, ra, p = RAIL
    return base + (rf if z >= 0 else ra) * (abs(z) / HALF_LENGTH) ** p


def inner_half_width(z):
    return max(0.0, 0.97 * half_width(z) - 0.12)


def bottom_y(z, abs_x):
    """Outside of the hull bottom at lateral distance abs_x, as HullShape.bottomY."""
    w, yk = half_width(z), keel_y(z)
    if w <= 0.1:
        return yk
    s = BOTTOM_SECTION
    if abs_x >= s[-1][0] * w:
        return s[-1][1] * yk
    for (x0, y0), (x1, y1) in zip(s, s[1:]):
        if abs_x <= x1 * w:
            f = (abs_x - x0 * w) / ((x1 - x0) * w)
            return y0 * yk + (y1 - y0) * yk * f
    return s[-1][1] * yk


def oar_pivot(side, z=OARLOCK_Z):
    """The tholepin pivot of an oar (side +1 port, -1 starboard)."""
    return (side * (half_width(z) * 1.02 + 0.06), rail_y(z) + GUNWALE_H + 0.02, z)


def oar_dir(side):
    a = math.radians(OAR_DOWN_DEG)
    return (side * math.cos(a), -math.sin(a), 0.0)


def main():
    print("z, half width, rail, keel, bottom at 0.6:")
    for z in (-2.5, -2.0, -1.0, 0.0, 1.0, 2.0, 2.5):
        print("  {%.1f, %.6f, %.6f, %.6f, %.6f}," % (z, half_width(z), rail_y(z), keel_y(z), bottom_y(z, 0.6)))
    for side in (1, -1):
        p = oar_pivot(side)
        print("oar pivot", side, "%.6f %.6f %.6f" % p)


if __name__ == "__main__":
    main()
