"""Hull shape and layout of the Royal Lion Ship (royal_lion_ship, "Navire royal au lion"), shared by the model
generator (tools/generate_royal_lion.py), the interior grid (tools/royal_lion_interior.py) and the furniture
(tools/royal_lion_decor.py).

MUST stay identical to fr.medievalships.core.RoyalLionLayout (Java), which uses the same formulas and numbers for
the hull probes, the buoyancy, the seats and the autopilot (checked by RoyalLionShipTest;
`python3 tools/royal_lion_shape.py` prints the reference values).

Ship-local coordinates, in blocks: x = lateral (+x = port / babord), y = up (0 = the waterline), z = forward
(+z = bow). See docs/RoyalLion_PLAN.md for the measurements of the four reference pictures.

Levels (all on the 0.5 block cells of the interior grid):
  roundhouse roof 12.0 (decorative, blue mansard roof) | quarterdeck 8.5 (helm, under the striped awning; the
  roundhouse - the royal state room, 8 blocks long - over its aft part) | forecastle 7.0 | main deck 5.0 (the
  captain's cabin under the quarterdeck opens on it) | lower deck 1.5 (crew quarters aft, cargo hold forward) |
  keel -3.6

P4 (deep fidelity pass): higher freeboard (every level 0.5 higher, the rail 6.7 amidships), a strong sheer rising
3.6 to the bow and 1.2 to the stern (the stubby, crescent hull of 044 and 126), the masts spread as on the pictures
(fore 12.5, main -0.5, mizzen -11.5 at the front of the castle's upper storey), the stern castle 12 blocks long with
an upper storey of 8 (the state room) over it.
"""
import math

# ---- hull (HullShape parameters): 40 blocks long (52 with the bowsprit), 12 wide
HALF_LENGTH = 20.0
TIP = 21.0
MAX_HALF_WIDTH = 6.0
FORE_SCALE, FORE_POW_A, FORE_POW_B = 20.6, 2.6, 0.6     # a full, rounded bow (the bluff bow of the references)
AFT_SCALE, AFT_POW_A, AFT_POW_B = 25.0, 4.0, 0.5        # a wide stern under the big castle (transom 9.2 wide)
KEEL_DEPTH, KEEL_RISE, KEEL_POW = 3.6, 2.6, 2.6      # the keel rises earlier to the ends: a shorter waterline
WATERLINE_Y = 0.0
RAIL_BASE, RAIL_RISE_FORE, RAIL_RISE_AFT, RAIL_POW = 6.7, 3.6, 1.2, 2.0   # P4: the strong sheer of 044 / 126
BOTTOM_SECTION = [(0.0, 1.0), (0.45, 0.9), (0.8, 0.55), (0.97, 0.12)]

# ---- decks and levels
CELL = 0.5
SLAB = 0.5                 # every deck is one cell thick
MAIN_DECK_Y = 5.0
LOWER_FLOOR_Y = 1.5        # the lower deck: the crew quarters (aft) and the cargo hold (forward)
QUARTERDECK_Y = 8.5        # over the captain's cabin
CABIN_FLOOR_Y = 5.0        # the captain's cabin opens on the main deck, no step
FORECASTLE_Y = 7.0         # the raised forecastle (solid under it), four steps over the main deck
ROUNDHOUSE_FLOOR_Y = QUARTERDECK_Y   # the royal state room on the quarterdeck, under the blue roof
ROUNDHOUSE_CEIL_Y = 12.0      # P4: a tall upper storey (3.5) with big arched windows, as on 126 and 071
ROOF_TOP_Y = 13.5          # top of the blue mansard roof (decorative, not walkable)
SHEER_BASE = 5.5           # top of the planking amidships (the bulwark rises above it to the rail)
BULWARK_TOP = 6.5          # collision top of the waist bulwarks (1.5 over the main deck)
FC_BULWARK_TOP = 8.2       # and of the forecastle's
QD_BULWARK_TOP = 9.6       # and of the quarterdeck balustrade
TRANSOM_Z = -20.0
CABIN_FRONT_Z = -8.0       # bulkhead of the captain's cabin / front of the quarterdeck (the castle is 12 long)
ROUNDHOUSE_FRONT_Z = -12.0  # front wall of the roundhouse (the royal state room: the upper storey, 8 long)
FORECASTLE_Z = 13.0        # aft edge of the forecastle
DECK_MAX_Z = 19.5
LOWER_AFT_Z = -15.0        # the lower deck, from the crew quarters' aft wall
LOWER_FORE_Z = 14.5        # to the hold's forward wall
BULKHEAD_Z = (-3.0, -2.5)  # the bulkhead between the crew quarters and the hold (a double door in it)

# ---- masts (z, top y) and the bowsprit: three masts as on the references (the fore and main masts with a course
# and a topsail each and a gold-railed fighting top, the mizzen with a course), stepped on the keel (fore, main)
# and on the quarterdeck (mizzen)
FORE_MAST_Z, FORE_MAST_TOP = 12.5, 29.5
MAIN_MAST_Z, MAIN_MAST_TOP = -0.5, 30.5
MIZZEN_Z, MIZZEN_TOP = -11.5, 26.0   # at the front of the upper storey, between its two doors
BOWSPRIT_FOOT = (0.0, 9.0, 17.5)
BOWSPRIT_TIP = (0.0, 14.8, 31.0)    # the jib-boom end (51 blocks over all)
STERN_REACH_Z = -21.4               # how far aft the rudder, the stern gallery and the lanterns reach

# ---- helm and pilot (quarterdeck, under the awning, forward of the mizzen, the pilot aft of the wheel)
HELM_Z = -9.4
PILOT_Z = -10.2

# ---- stairs (grid: 0.5 high, 0.5 deep steps)
QD_STAIR_X = (2.5, 4.0)                 # both sides, main deck -> quarterdeck (7 steps, rising aft)
QD_STAIR_Z = (CABIN_FRONT_Z + 3.5, CABIN_FRONT_Z)
FC_STAIR_X = (2.0, 3.5)                 # both sides, main deck -> forecastle (4 steps, rising forward)
FC_STAIR_Z = (FORECASTLE_Z - 2.0, FORECASTLE_Z)
CREW_STAIR_X = (-2.2, -0.7)             # main deck -> crew quarters (7 steps, going down aft), starboard of the centre
CREW_STAIR_Z = (-7.0, -3.5)
HOLD_STAIR_X = (2.0, 3.5)               # main deck -> cargo hold (7 steps, going down aft), port side
HOLD_STAIR_Z = (3.5, 7.0)

# ---- the shields (blue, a gold rampant lion) along each side, the lit ports and the lanterns between them
SHIELD_Z = (-5.5, 0.5, 6.5, 12.5)        # on the waist and the forecastle (the castle has its windows and banners)
SHIELD_Y = 4.6
BANNER_Z = (-2.5, 3.5, 9.5)              # the hanging lion banners between the shields (044, 123, 126)
PORT_Z = (-17.0, -11.5, -2.5, 3.5, 9.5, 15.3)
PORT_Y = 1.45


def half_width(z):
    fore = z >= 0
    a = abs(z) / (FORE_SCALE if fore else AFT_SCALE)
    if a >= 1.0:
        return 0.0
    pa, pb = (FORE_POW_A, FORE_POW_B) if fore else (AFT_POW_A, AFT_POW_B)
    return MAX_HALF_WIDTH * (1.0 - a ** pa) ** pb


def rail_y(z):
    a = min(1.0, abs(z) / HALF_LENGTH)
    rise = RAIL_RISE_FORE if z >= 0 else RAIL_RISE_AFT
    return RAIL_BASE + rise * a ** RAIL_POW


def sheer_y(z):
    """Top of the planking (the deck edge with its gold planksheer); the bulwark rises from it to rail_y."""
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


def deck_y(z):
    """Walking deck height at z (main deck; the quarterdeck aft of the cabin front, the forecastle forward)."""
    if z < CABIN_FRONT_Z:
        return QUARTERDECK_Y
    if z > FORECASTLE_Z:
        return FORECASTLE_Y
    return MAIN_DECK_Y


# ---- cross section of the outer hull (model and grid)
TUMBLE = 0.4        # the topsides lean inboard by this much at the sheer (tumblehome)


def section_points(z):
    """(x, y) of the outer hull section at z (one side, x >= 0), from the keel up to the sheer."""
    w, yk, ys = half_width(z), keel_y(z), sheer_y(z)
    pts = [(0.18, yk)]
    for fx, fy in BOTTOM_SECTION[1:]:
        pts.append((max(0.18, fx * w), fy * yk))
    pts.append((max(0.18, 0.995 * w), 0.6))
    for t in (0.25, 0.5, 0.75, 1.0):
        y = 0.6 + (ys - 0.6) * t
        pts.append((max(0.18, w - TUMBLE * w / MAX_HALF_WIDTH * t ** 1.6), y))
    return pts


BOW_RAKE = (0.42, 0.3)   # the bow leans forward: the stem moves ahead by this much per block above (below) the water


def rake(z, y):
    """How far forward the bow sections are moved at height y (0 aft of the fore body)."""
    f = min(1.0, max(0.0, (z - 6.0) / 11.0)) ** 1.5
    return f * (BOW_RAKE[0] * y if y > 0 else BOW_RAKE[1] * y)


def hull_x(z, y):
    """Outer half width of the hull at height y (0 below the keel); above the sheer the bulwark continues the
    topside (same lean). The bow sections lean forward (raked stem)."""
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
    xa, ya = pts[-2]
    xb, yb = pts[-1]
    return xb + (xb - xa) / max(1e-9, yb - ya) * (y - yb)


if __name__ == "__main__":
    for z in (-20.0, -12.0, 0.0, 10.5, 17.0):
        print(z, round(half_width(z), 6), round(rail_y(z), 6), round(keel_y(z), 6), round(bottom_y(z, 2.0), 6))
