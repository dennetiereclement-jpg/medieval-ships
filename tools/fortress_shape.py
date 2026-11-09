"""Hull shape and layout of the Fortress Ship (fortress_ship), shared by the model generator
(tools/generate_fortress.py) and the interior grid (tools/fortress_interior.py).

MUST stay identical to fr.medievalships.core.FortressLayout (Java), which uses the same formulas and
numbers for the hull probes, the buoyancy, the seats and the autopilot (checked by FortressShipTest;
`python3 tools/fortress_shape.py` prints the reference values).

Ship-local coordinates, in blocks: x = lateral (+x = port / babord), y = up (0 = the waterline),
z = forward (+z = bow). See docs/Fortress_PLAN.md for the measurements of the references.

A floating castle that keeps a ship's shape: a massive, beamy hull (43 blocks, 48.5 with the bowsprit, 13
wide) with a strongly raked bow, clad with grey stone wales and ribs; a raised forecastle; a two storey stern
castle (the captain's cabin under the quarterdeck, the keep with its battlements over the aft part of it) and
a turret with a pointed red roof on the keep.

Levels (all on the 0.5 block cells of the interior grid):
  turret / keep roof 11.0 | quarterdeck 8.0 (over the captain's cabin) | forecastle 7.0 (over the crew's
  mess) | main deck 4.5 (the waist, the captain's cabin and the mess open on it) | lower deck 1.0 (the cargo
  hold and the crew quarters) | keel -3.0
"""
import math

# ---- hull (HullShape parameters): 43 blocks over the raked stem and the castle (48.5 with the bowsprit), 13 wide
HALF_LENGTH = 19.0
TIP = 22.5
MAX_HALF_WIDTH = 6.5
FORE_SCALE, FORE_POW_A, FORE_POW_B = 18.5, 2.4, 0.62
AFT_SCALE, AFT_POW_A, AFT_POW_B = 24.0, 3.4, 0.5
KEEL_DEPTH, KEEL_RISE, KEEL_POW = 3.0, 2.0, 3.0
WATERLINE_Y = 0.0
RAIL_BASE, RAIL_RISE_FORE, RAIL_RISE_AFT, RAIL_POW = 5.5, 2.5, 0.0, 3.0
BOTTOM_SECTION = [(0.0, 1.0), (0.5, 0.88), (0.82, 0.5), (0.97, 0.1)]

# ---- decks and levels
CELL = 0.5
SLAB = 0.5                 # every deck is one cell thick
MAIN_DECK_Y = 4.5          # the waist
LOWER_FLOOR_Y = 1.0        # the cargo hold and the crew quarters
FORECASTLE_Y = 7.0         # over the crew's mess
QUARTERDECK_Y = 8.0        # over the captain's cabin
KEEP_Y = 11.0              # the keep's roof (battlements) and the turret's floor
CABIN_FLOOR_Y = 4.5        # the captain's cabin and the mess open on the waist, no step
WAIST_TOP = 5.5            # top of the stone gunwale of the waist (stone merlons stand on it)
FC_TOP = 7.5               # stone curb of the forecastle (the wooden balustrade stands on it)
QD_TOP = 9.0               # stone parapet of the quarterdeck (merlons over it)
KEEP_TOP = 12.0            # stone parapet of the keep (merlons over it)
TRANSOM_Z = -19.5
CABIN_FRONT_Z = -9.0       # front bulkhead of the castle (the captain's cabin) / front of the quarterdeck
KEEP_FRONT_Z = -13.0       # front wall of the keep (the officers' room) / aft end of the open quarterdeck
FC_FRONT_Z = 6.0           # aft bulkhead of the forecastle (the mess); the fore mast stands on the forecastle
DECK_MAX_Z = 19.0
CREW_BULKHEAD_Z = 5.5      # between the cargo hold (aft) and the crew quarters (forward), on the lower deck
STEM_HEAD_Z = 22.5         # the stone beak at the head of the raked stem

# ---- the turret on the keep (x half width, z range) and its roof
TURRET_HALF = 2.5
TURRET_Z = (-19.0, -15.0)
TURRET_WALL_TOP = 14.5
TURRET_ROOF_TOP = 17.0

# ---- masts (z, top y) and the bowsprit: three masts as on the references. The fore and main masts are
# stepped on the keel (through the lower deck), the mizzen on the quarterdeck.
FORE_MAST_Z, FORE_MAST_TOP = 8.0, 24.0
MAIN_MAST_Z, MAIN_MAST_TOP = -1.0, 27.5
MIZZEN_Z, MIZZEN_TOP = -11.5, 24.5
BOWSPRIT_FOOT = (0.0, 8.4, 19.5)
BOWSPRIT_TIP = (0.0, 11.6, 28.0)

# ---- helm and pilot (quarterdeck, between the wheel and the mizzen)
HELM_Z = -9.7
PILOT_Z = -10.5

# ---- stairs (grid: 0.5 high, 0.5 deep steps)
QD_STAIR_X = (3.0, 4.5)              # both sides, main deck -> quarterdeck (7 steps, rising aft)
QD_STAIR_Z = (CABIN_FRONT_Z + 3.5, CABIN_FRONT_Z)
FC_STAIR_X = (2.5, 4.0)              # both sides, main deck -> forecastle (5 steps, rising forward)
FC_STAIR_Z = (FC_FRONT_Z - 2.5, FC_FRONT_Z)
KEEP_STAIR_X = (2.5, 4.0)            # inside the keep, along its port wall: officers' room -> keep's roof (6 steps, rising aft)
KEEP_STAIR_Z = (-15.0, -17.5)        # (foot, top): the hatch in the roof over its upper steps
KEEP_HATCH_Z = (-17.5, -14.5)        # the hatch in the keep's roof: over the stair and half a block before its foot (head room)
COMPANION_X = (2.5, 4.0)             # main deck -> lower deck (7 steps, going down aft), port side abaft the main mast
COMPANION_Z = (-5.0, -1.5)

# ---- the stone ribs (buttresses) on the hull sides, between the red panels
RIB_Z = (-19.0, -14.4, -9.6, -4.8, 0.2, 5.0, 10.2, 15.0)
FC_LEVEL_END = 14.0                   # the forecastle's curb is level up to here, then sweeps up to the beak
SHEER_RAMP = (4.5, 6.5)              # the stone belt climbs from the waist to the forecastle between these z


def half_width(z):
    fore = z >= 0
    a = abs(z) / (FORE_SCALE if fore else AFT_SCALE)
    if a >= 1.0:
        return 0.0
    pa, pb = (FORE_POW_A, FORE_POW_B) if fore else (AFT_POW_A, AFT_POW_B)
    return MAX_HALF_WIDTH * (1.0 - a ** pa) ** pb


def rail_y(z):
    """HullShape.railY without the raised floors (the Java side adds the castles' rail floors)."""
    a = min(1.0, abs(z) / HALF_LENGTH)
    rise = RAIL_RISE_FORE if z >= 0 else RAIL_RISE_AFT
    return RAIL_BASE + rise * a ** RAIL_POW


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


def smooth(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


def sheer_y(z):
    """Top of the hull side (the stone gunwale): the waist level aft (the castle's walls rise from it), climbing
    to the forecastle's curb and sweeping up to the stone beak at the stem head (the bow of the reference)."""
    fc = WAIST_TOP + (FC_TOP - WAIST_TOP) * smooth((z - SHEER_RAMP[0]) / (SHEER_RAMP[1] - SHEER_RAMP[0]))
    if z > FC_LEVEL_END:
        fc += 2.6 * ((z - FC_LEVEL_END) / (STEM_HEAD_Z - FC_LEVEL_END)) ** 1.8
    return fc


# ---- cross section of the outer hull (model and grid)
TUMBLE = 0.45       # the topsides lean inboard by this much at the sheer (tumblehome)


def section_points(z):
    """(x, y) of the outer hull section at z (one side, x >= 0), from the keel up to the sheer."""
    w, yk, ys = half_width(z), keel_y(z), sheer_y(z)
    pts = [(0.2, yk)]
    for fx, fy in BOTTOM_SECTION[1:]:
        pts.append((max(0.2, fx * w), fy * yk))
    pts.append((max(0.2, 0.995 * w), 0.5))
    for t in (0.25, 0.5, 0.75, 1.0):
        y = 0.5 + (ys - 0.5) * t
        pts.append((max(0.2, w - TUMBLE * w / MAX_HALF_WIDTH * t ** 1.6), y))
    return pts


BOW_RAKE = (0.42, 0.3)   # the bow leans forward: the stem moves ahead by this much per block above (below) the water


def rake(z, y):
    """How far forward the bow sections are moved at height y (0 aft of the fore body)."""
    f = min(1.0, max(0.0, (z - 6.0) / 10.0)) ** 1.5
    return f * (BOW_RAKE[0] * y if y > 0 else BOW_RAKE[1] * y)


def hull_x(z, y):
    """Outer half width of the hull at height y (0 below the keel); above the sheer the bulwarks and the castle's
    walls rise straight up from it. The bow sections lean forward (raked stem)."""
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
    return pts[-1][0]   # above the sheer: the bulwarks, the castle's walls and parapets rise straight up


def stem_z(y):
    """z of the raked stem (where the planking closes) at height y."""
    return FORE_SCALE - 0.02 + rake(FORE_SCALE, y)


if __name__ == "__main__":
    for z in (-19.5, -11.0, 0.0, 9.5, 16.0):
        print(z, round(half_width(z), 6), round(rail_y(z), 6), round(keel_y(z), 6), round(bottom_y(z, 2.0), 6))
    print("stem head", round(stem_z(sheer_y(STEM_HEAD_Z)), 3), "sheer at the head", round(sheer_y(STEM_HEAD_Z), 3))
    for z in (-19.5, -9.0, 0.0, 11.0, 15.0, 18.0):
        print("hull_x at main deck", z, round(hull_x(z, MAIN_DECK_Y), 3), "at 1.0", round(hull_x(z, 1.0), 3))
