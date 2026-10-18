"""Shape and layout of the Nautilus (nautilus), shared by the model generator and the interior grid.

MUST stay identical to Ships.NautilusLayout (Java), which uses the same formulas for the terrain
probes, the buoyancy and the autopilot (checked by NautilusTest).

Ship-local coordinates, in blocks: x = lateral (+x = port), y = up (0 = floor of the main level),
z = forward (+z = bow). The hull is a body with elliptical cross sections: half width W(z), half
height H(z) about the axis y = AXIS_Y. Option C of docs/NAUTILUS_PLAN.md: 96 blocks overall
(ram and tail fin included), 14 wide, 17 high, 23 with the wheelhouse.
"""
import math

# ---- hull body
BOW_Z = 42.0             # end of the hull body at the bow (the ram goes on)
STERN_Z = -44.0          # end of the hull body at the stern (the tail cone and the fin go on)
MAX_HALF_WIDTH = 7.0
MAX_HALF_HEIGHT = 8.5
AXIS_Y = 0.5             # hull from -8.0 to 9.0 at the widest section
FORE = (2.2, 0.6)        # scale(z) = (1 - t^a)^b, t = z / BOW_Z ahead of the middle
AFT = (2.0, 0.55)        # and t = -z / -STERN_Z behind it
SHELL = 0.5              # thickness of the pressure hull
RAM_TIP_Z = 48.0
TAIL_END_Z = -48.0

# ---- levels (floor heights)
BILGE_FLOOR_Y = -7.0     # double bottom: crawlway between the ballast tanks
LOWER_FLOOR_Y = -4.5
MAIN_FLOOR_Y = 0.0
LEVEL_HEIGHT = 4.5

# ---- floating: local height of the water surface when surfaced (just under the main floor)
WATERLINE_Y = -0.2

CELL = 0.5


def scale(z):
    if z >= 0:
        t, (a, b) = z / BOW_Z, FORE
    else:
        t, (a, b) = -z / -STERN_Z, AFT
    if t >= 1.0:
        return 0.0
    return (1.0 - t ** a) ** b


def half_width(z):
    return MAX_HALF_WIDTH * scale(z)


def half_height(z):
    return MAX_HALF_HEIGHT * scale(z)


def inside_hull(x, y, z, inset=0.0):
    """Is the point inside the hull (shrunk by inset)?"""
    w, h = half_width(z) - inset, half_height(z) - inset
    if w <= 0 or h <= 0:
        return False
    return (x / w) ** 2 + ((y - AXIS_Y) / h) ** 2 <= 1.0


def hull_top(z, x=0.0):
    w, h = half_width(z), half_height(z)
    if w <= abs(x):
        return AXIS_Y
    return AXIS_Y + h * math.sqrt(1.0 - (x / w) ** 2)


def hull_bottom(z, x=0.0):
    return 2 * AXIS_Y - hull_top(z, x)


if __name__ == "__main__":
    for z in (-40.0, -20.0, 0.0, 20.0, 40.0):
        print("{%s, %.6f, %.6f}," % (z, half_width(z), half_height(z)))
