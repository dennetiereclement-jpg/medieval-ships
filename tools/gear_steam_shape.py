"""Hull shape and layout of the Gear Steamship (gear_steamship), shared by the model generator
(tools/generate_gear_steam.py), the interior grid (tools/gear_steam_interior.py) and the furniture
(tools/gear_steam_decor.py).

MUST stay identical to fr.medievalships.core.GearSteamLayout (Java), which uses the same formulas and
numbers for the hull probes, the buoyancy, the seats and the autopilot (checked by GearSteamShipTest;
`python3 tools/gear_steam_shape.py` prints the reference values).

Ship-local coordinates, in blocks: x = lateral (+x = port / babord), y = up (0 = the waterline),
z = forward (+z = bow). See docs/GearSteam_PLAN.md for the measurements of the reference (one starboard
view at sunset; the port side is its mirror).

Levels (all on the 0.5 block cells of the interior grid):
  bridge 11.0 (the roof of the captain's deckhouse, the helm) | engine house roof 9.0 (the copper dome)
  | poop deck 7.5 (aft, over the crew quarters) | forecastle 6.0 | main deck 4.5 (the waist, the engine
  room and the crew quarters) | hold 1.0 (the lower deck) | keel -3.0
"""
import math

# ---- hull (HullShape parameters): 35 blocks at the waterline, 42 from the stern gallery to the stem head
# (45 with the bow boom), 10 wide; an iron-plated, nearly wall-sided hull with a raked stem and a counter
HALF_LENGTH = 18.0
TIP = 19.0
MAX_HALF_WIDTH = 5.0
FORE_SCALE, FORE_POW_A, FORE_POW_B = 18.8, 2.4, 0.62
AFT_SCALE, AFT_POW_A, AFT_POW_B = 24.0, 3.2, 0.5
KEEL_DEPTH, KEEL_RISE, KEEL_POW = 3.0, 2.6, 3.0
WATERLINE_Y = 0.0
RAIL_BASE, RAIL_RISE_FORE, RAIL_RISE_AFT, RAIL_POW = 5.5, 1.5, 0.0, 4.0
BOTTOM_SECTION = [(0.0, 1.0), (0.5, 0.92), (0.82, 0.6), (0.97, 0.15)]

# ---- decks and levels
CELL = 0.5
SLAB = 0.5                 # every deck is one cell thick
HOLD_FLOOR_Y = 1.0         # the lower deck: the cargo hold
MAIN_DECK_Y = 4.5          # the waist, the engine room, the crew quarters
FORECASTLE_Y = 6.0
POOP_Y = 7.5               # over the crew quarters
ENGINE_ROOF_Y = 9.0        # the roof of the engine house (the dome stands on it)
BRIDGE_Y = 11.0            # the roof of the captain's deckhouse: the bridge with the helm
CABIN_FLOOR_Y = POOP_Y     # the captain's cabin is the deckhouse on the poop deck

TRANSOM_Z = -17.5          # the stern of the hull (the poop's taffrail)
GALLERY_Z = -20.0          # the aft face of the stern gallery (a balcony off the crew quarters, under the poop's overhang)
POOP_FRONT_Z = -6.5        # the poop ends against the engine house
ENGINE_FRONT_Z = 5.0       # the front wall of the engine house, on the waist
FORECASTLE_Z = 11.5        # the front of the waist / the forecastle's break
DECK_MAX_Z = 19.5          # the forecastle deck ends at the stem
DECKHOUSE_Z = (-14.0, -7.0)    # the captain's deckhouse on the poop
DECKHOUSE_HALF = 3.0

WAIST_BULWARK_TOP = 6.0    # collision tops of the bulwarks (the copper railings drawn on them rise higher)
WAIST_CAP_Y = 5.5          # the riveted copper cap of the waist bulwark
FORECASTLE_BULWARK_TOP = 7.5
FORECASTLE_CAP_Y = 7.0
POOP_BULWARK_TOP = 8.5
POOP_CAP_Y = 8.0
ENGINE_RAIL_TOP = 10.0      # the railing round the engine house roof
BRIDGE_RAIL_TOP = 12.0     # and round the bridge
GALLERY_BULWARK_TOP = 6.0

# ---- masts, funnel, dome, crane, bow boom (as measured on the reference)
MAIN_MAST_Z, MAIN_MAST_TOP = 7.5, 19.6     # stepped on the keel, through the hold and the waist
MIZZEN_Z, MIZZEN_TOP = -15.9, 18.0         # stepped on the poop deck
MAIN_YARD_Y, MAIN_SAIL_FOOT = 17.2, 9.6
MIZZEN_YARD_Y, MIZZEN_SAIL_FOOT = 15.5, 10.4
MAIN_YARD_HALF, MIZZEN_YARD_HALF = 5.6, 3.0
YARD_TILT_DEG = 22.0       # and peaked: the aft (starboard) arm higher, the sails slanting down forward
BRACE_DEG = 62.0           # the yards are braced round, the starboard arms aft: the sails show their faces to starboard
FUNNEL_Z, FUNNEL_R, FUNNEL_TOP = -5.6, 1.4, 18.0
DOME_Z, DOME_R, DOME_TOP = -0.9, 2.85, 14.2
CRANE_Z = -18.8                            # the crane's post on the poop deck (over the gallery), its jib reaching over the stern
CRANE_TIP = (0.0, 12.8, -23.6)
CRATE_Y = (7.2, 8.5)
STEM_HEAD = (0.0, 10.9, 22.0)              # top of the raised prow
BOOM_TIP = (0.0, 10.7, 25.2)               # the bow boom carrying the great lantern
STERN_REACH_Z = -24.4                      # the hanging crate, the furthest aft
BIG_GEAR = (4.5, -0.4, 2.0)                # (y, z, radius) of the big brass gear on each side
BOW_GEAR = (5.8, 17.4, 1.1)

# ---- helm and pilot (the bridge, at the front of the deckhouse roof)
HELM_Z = -8.5
PILOT_Z = -9.3

# ---- stairs and ladders (grid: 0.5 high, 0.5 deep steps)
FC_STAIR_X = (1.5, 3.0)                    # both sides, waist -> forecastle (3 steps, rising forward)
FC_STAIR_Z = (FORECASTLE_Z - 1.5, FORECASTLE_Z)
COMPANION_X = (1.5, 3.0)                   # waist -> hold (7 steps, going down forward), port side
COMPANION_Z = (6.0, 9.5)
ENGINE_STAIR_X = (-3.5, -2.0)              # engine room -> hold (7 steps, going down aft), starboard side
ENGINE_STAIR_Z = (-1.0, -4.5)
POOP_STEP_X = (3.0, 4.5)                   # engine house roof -> poop deck (3 steps down aft), both sides
POOP_STEP_Z = (POOP_FRONT_Z, POOP_FRONT_Z - 1.0)
ROOF_LADDER_X = (2.5, 3.5)                 # waist -> engine house roof: a ladder on the front wall, both sides
ROOF_LADDER_Z = (ENGINE_FRONT_Z, ENGINE_FRONT_Z + 0.5)
BRIDGE_LADDER_X = (1.5, 2.5)               # poop deck -> bridge: a ladder on the deckhouse's aft wall (port)
BRIDGE_LADDER_Z = (DECKHOUSE_Z[0] - 0.5, DECKHOUSE_Z[0])


def half_width(z):
    fore = z >= 0
    a = abs(z) / (FORE_SCALE if fore else AFT_SCALE)
    if a >= 1.0:
        return 0.0
    pa, pb = (FORE_POW_A, FORE_POW_B) if fore else (AFT_POW_A, AFT_POW_B)
    return MAX_HALF_WIDTH * (1.0 - a ** pa) ** pb


def rail_y(z):
    """HullShape's sheer (the waist bulwark cap, rising a little at the bow): the castles add their own
    bulwarks (top_y)."""
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


COUNTER_Z, COUNTER_SLOPE = -15.8, 1.3


def keel_draw(z):
    """The drawn keel line: keel_y, raised aft into the counter (the stern overhangs the water: the hull leaves
    the sea about z = -16, its transom bottom about 2 blocks up). Python only (the model and the grid); the
    Java HullShape keeps keel_y (a little deeper under the counter: buoyancy and placement only)."""
    k = keel_y(z)
    if z < COUNTER_Z:
        k = max(k, (COUNTER_Z - z) * COUNTER_SLOPE - 0.4)
    return k


def top_y(z):
    """Top of the drawn hull side at z (the riveted cap of each part): the poop, the engine house walls
    flush with the sides, the waist, the forecastle (the prow rises above it, drawn on its own)."""
    if z < POOP_FRONT_Z:
        return POOP_CAP_Y
    if z < ENGINE_FRONT_Z:
        return ENGINE_ROOF_Y
    if z < FORECASTLE_Z:
        return WAIST_CAP_Y
    return FORECASTLE_CAP_Y


# ---- cross section of the outer hull (model and grid)
TUMBLE = 0.1        # the topsides lean inboard a little


def section_points(z, ys=None):
    """(x, y) of the outer hull section at z (one side, x >= 0), from the keel up to the top."""
    w, yk = half_width(z), keel_draw(z)
    ys = top_y(z) if ys is None else ys
    pts = [(0.18, yk)]
    for fx, fy in BOTTOM_SECTION[1:]:
        pts.append((max(0.18, fx * w), fy * yk if yk < 0 else yk + 0.15 * (1 - fy)))
    y0 = max(0.5, pts[-1][1] + 0.1)
    pts.append((max(0.18, 0.995 * w), y0))
    for t in (0.25, 0.5, 0.75, 1.0):
        y = y0 + (ys - y0) * t
        pts.append((max(0.18, w - TUMBLE * w / MAX_HALF_WIDTH * t ** 1.6), y))
    return pts


BOW_RAKE = (0.30, 0.25)   # the stem leans forward by this much per block above (below) the water, up to RAKE_TOP
RAKE_TOP = 11.0


def rake(z, y):
    """How far forward the bow sections are moved at height y (0 aft of the fore body)."""
    f = min(1.0, max(0.0, (z - 4.0) / 12.0)) ** 1.5
    return f * (BOW_RAKE[0] * min(y, RAKE_TOP) if y > 0 else BOW_RAKE[1] * y)


def hull_x(z, y):
    """Outer half width of the hull at height y (0 below the keel); above the top the side goes on
    straight up (the walls of the castles). The bow sections lean forward (raked stem)."""
    return _hull_x(z - rake(z, y), y)


def _hull_x(z, y):
    if z > FORE_SCALE or z < -AFT_SCALE:
        return 0.0
    pts = section_points(z, 12.0)
    if y < pts[0][1]:
        return 0.0
    for (xa, ya), (xb, yb) in zip(pts[:-1], pts[1:]):
        if ya <= y <= yb:
            return xa + (xb - xa) * (y - ya) / max(1e-9, yb - ya)
    return pts[-1][0]


def stem_z(y):
    """z of the stem (the bow's extremity) at height y."""
    return FORE_SCALE + rake(FORE_SCALE, y)


if __name__ == "__main__":
    for z in (-19.0, -11.0, 0.0, 9.5, 16.0):
        print(z, round(half_width(z), 6), round(rail_y(z), 6), round(keel_y(z), 6), round(bottom_y(z, 2.0), 6))
    print("stem at the water", round(stem_z(0.0), 3), "at the forecastle cap", round(stem_z(FORECASTLE_CAP_Y), 3))
