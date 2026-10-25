"""Hull shape and layout of the Old Corsair (old_corsair), shared by the model generator and the
interior grid (tools/corsair_interior.py).

MUST stay identical to fr.medievalships.core.CorsairLayout (Java), which uses the same formulas and
numbers for the hull probes, the buoyancy, the seats and the autopilot (checked by CorsairTest;
`python3 tools/corsair_shape.py` prints the reference values).

Ship-local coordinates, in blocks: x = lateral (+x = port / babord), y = up (0 = the waterline),
z = forward (+z = bow). See docs/CORSAIR_PLAN.md for the measurements of the reference sheet.

Levels (all on the 0.5 block cells of the interior grid):
  quarterdeck 7.0 (over the captain's cabin, whose floor is 4.0) | main deck 4.5 | lower deck 1.0
  (common room, kitchen, crew, coursive) | hold -2.0 (below the waterline: dry thanks to the interior
  grid) | keel -3.4
"""
import math

# ---- hull (HullShape parameters)
HALF_LENGTH = 21.0
TIP = 22.0
MAX_HALF_WIDTH = 5.0
FORE_SCALE, FORE_POW_A, FORE_POW_B = 21.6, 3.2, 0.6
AFT_SCALE, AFT_POW_A, AFT_POW_B = 27.0, 4.0, 0.5
KEEL_DEPTH, KEEL_RISE, KEEL_POW = 3.4, 2.2, 3.0
WATERLINE_Y = 0.0
RAIL_BASE, RAIL_RISE_FORE, RAIL_RISE_AFT, RAIL_POW = 5.6, 2.4, 0.4, 2.8
BOTTOM_SECTION = [(0.0, 1.0), (0.45, 0.9), (0.8, 0.55), (0.97, 0.12)]

# ---- decks and levels
CELL = 0.5
MAIN_DECK_Y = 4.5
SLAB = 0.5                 # every deck is one cell thick
LOWER_FLOOR_Y = 1.0        # the lower deck (entrepont): common room, kitchen, crew, coursive
HOLD_FLOOR_Y = -2.0        # the hold (cale), below the waterline
QUARTERDECK_Y = 7.0        # over the captain's cabin
CABIN_FLOOR_Y = 4.0        # the cabin lies a step below the main deck
SHEER_BASE = 4.6           # top of the black planking amidships (the brown bulwark rises above it)
BULWARK_TOP = 6.0          # collision top of the waist bulwarks (the drawn cap rail is at RAIL_BASE)
QD_BULWARK_TOP = 8.5      # and of the quarterdeck balustrade
TRANSOM_Z = -21.0
CABIN_FRONT_Z = -14.0      # bulkhead of the captain's cabin / front of the quarterdeck
DECK_MAX_Z = 20.5

# ---- masts (z, foot y, top y) and the bowsprit
FORE_MAST_Z, FORE_MAST_TOP = 11.5, 33.5
MAIN_MAST_Z, MAIN_MAST_TOP = 2.5, 34.6
MIZZEN_Z, MIZZEN_TOP = -7.5, 30.0
BOWSPRIT_FOOT = (0.0, 5.8, 18.4)
BOWSPRIT_TIP = (0.0, 10.4, 30.8)

# ---- helm and pilot (quarterdeck)
HELM_Z = -15.3
PILOT_Z = -16.1

# ---- stairs (grid: 0.5 high, 0.5 deep steps)
QD_STAIR_X = (2.0, 3.5)                 # both sides, main deck -> quarterdeck (5 steps, rising aft)
QD_STAIR_Z = (CABIN_FRONT_Z + 2.5, CABIN_FRONT_Z)
COMPANION_X = (2.0, 3.5)                # main deck -> common room (7 steps, going down aft)
COMPANION_Z = (1.0, 4.5)
HOLD_STAIR_X = (-1.0, 1.0)              # lower deck -> hold, at the aft end of the coursive (6 steps, going down aft)
HOLD_STAIR_Z = (-17.0, -14.0)


def half_width(z):
    fore = z >= 0
    a = abs(z) / (FORE_SCALE if fore else AFT_SCALE)
    if a >= 1.0:
        return 0.0
    pa, pb = (FORE_POW_A, FORE_POW_B) if fore else (AFT_POW_A, AFT_POW_B)
    return MAX_HALF_WIDTH * (1.0 - a ** pa) ** pb


def rail_y(z):
    a = min(1.0, abs(z) / HALF_LENGTH)   # (the raked bow goes beyond HALF_LENGTH at the top)
    rise = RAIL_RISE_FORE if z >= 0 else RAIL_RISE_AFT
    return RAIL_BASE + rise * a ** RAIL_POW


def sheer_y(z):
    """Top of the black planking (the deck edge); the brown bulwark rises from it to rail_y."""
    return rail_y(z) - (RAIL_BASE - SHEER_BASE)


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


# ---- cross section of the outer hull (model and grid)
TUMBLE = 0.32       # the topsides lean inboard by this much at the sheer (tumblehome)


def section_points(z):
    """(x, y) of the outer hull section at z (one side, x >= 0), from the keel up to the sheer."""
    w, yk, ys = half_width(z), keel_y(z), sheer_y(z)
    pts = [(0.18, yk)]
    for fx, fy in BOTTOM_SECTION[1:]:
        pts.append((max(0.18, fx * w), fy * yk))
    pts.append((max(0.18, 0.995 * w), 0.45))
    for t in (0.25, 0.5, 0.75, 1.0):
        y = 0.45 + (ys - 0.45) * t
        pts.append((max(0.18, w - TUMBLE * w / MAX_HALF_WIDTH * t ** 1.6), y))
    return pts


BOW_RAKE = (0.42, 0.3)   # the bow leans forward: the stem moves ahead by this much per block above (below) the water


def rake(z, y):
    """How far forward the bow sections are moved at height y (0 aft of the fore body)."""
    f = min(1.0, max(0.0, (z - 6.0) / 12.0)) ** 1.5
    return f * (BOW_RAKE[0] * y if y > 0 else BOW_RAKE[1] * y)


def hull_x(z, y):
    """Outer half width of the hull at height y (0 below the keel); above the sheer the bulwark
    continues the topside (same lean). The bow sections lean forward (raked stem)."""
    return _hull_x(z - rake(z, y), y)


def _hull_x(z, y):
    if z > FORE_SCALE:
        return 0.0
    pts = section_points(z)
    if y < pts[0][1]:
        return 0.0
    for (xa, ya), (xb, yb) in zip(pts[:-1], pts[1:]):
        if ya <= y <= yb:
            return xa + (xb - xa) * (y - ya) / max(1e-9, yb - ya)
    # above the sheer: the bulwark, leaning on
    xa, ya = pts[-2]
    xb, yb = pts[-1]
    return xb + (xb - xa) / max(1e-9, yb - ya) * (y - yb)


if __name__ == "__main__":
    for z in (-21.0, -13.0, 0.0, 11.5, 19.0):
        print(z, round(half_width(z), 6), round(rail_y(z), 6), round(keel_y(z), 6), round(bottom_y(z, 2.0), 6))
