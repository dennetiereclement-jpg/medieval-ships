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
BOW_Z = 41.5             # end of the hull body at the bow (the ram goes on)
STERN_Z = -35.0          # end of the hull body at the stern (the tail cone and the fin go on)
MAX_HALF_WIDTH = 7.0
MAX_HALF_HEIGHT = 7.75
AXIS_Y = -0.25           # hull from -8.0 to 7.5 at the widest section, the casing on top to 9.0
FORE = (2.8, 0.55)       # scale(z) = (1 - t^a)^b, t = z / BOW_Z ahead of the middle
AFT = (4.0, 0.45)        # and t = -z / -STERN_Z behind it
SHELL = 0.5              # thickness of the pressure hull
RAM_TIP_Z = 48.0
TAIL_END_Z = -48.0
# tail: a cone with rings from the end of the hull to the propeller, then the fish-tail fin
TAIL_CONE_Z = -39.8      # end of the cone, the propeller just behind it
PROP_Z = -40.4
PROP_R = 3.2
FIN_Z0 = -41.6           # leading edge of the tail fin (root)
FIN_TIP_LE_Z = -45.8      # leading edge at the tip of a lobe
FIN_TIP_TE_Z = -47.8      # trailing edge at the tip of a lobe
FIN_NOTCH_Z = -44.8       # trailing edge at the root (the notch of the fish tail)
FIN_TOP = 9.6            # tips of the fin lobes above / below the axis
FIN_BOTTOM = -8.4
FIN_SPAN = 6.5           # horizontal tail fins, beyond the axis on each side

# ---- raised casing along the top of the hull (a flat deck), the wheelhouse and the projector cage on it
CASING_HALF_WIDTH = 2.0
CASING_TOP_Y = 9.0
CASING_Z = (-24.0, 27.0)
TOWER_Z = (15.0, 22.5)   # wheelhouse
TOWER_HALF_WIDTH = 2.5
TOWER_TOP_Y = 12.5
LAMP_CAGE_Z = (10.0, 14.2)  # projector cage behind the wheelhouse, its lens above the wheelhouse roof
LAMP_CAGE_HALF_WIDTH = 1.5
LAMP_CAGE_TOP_Y = 14.2
LENS_Y = 13.0
# crests of spikes: (z0, z1, rise): the fore one climbs from the hull to the top of the wheelhouse front
FORE_CREST = (31.5, 22.6)
AFT_CREST = (-2.0, -13.0)
# windows: the great salon window (centre z, y, radius) on each side; the row of small windows
SALON_WINDOW = (0.0, 2.6, 2.9)
SMALL_WINDOWS_Y = -2.3
SMALL_WINDOWS_Z = (29.0, 26.5, 24.0, 21.5, 19.0, 16.5, 14.0, 11.5, 9.0, 6.5)
CABIN_PORTHOLES = ((23.2, 2.0),)       # (z, y): one in each cabin of the main level, on both sides
TOWER_WINDOWS_Y = (9.75, 11.25)        # the four large windows of the wheelhouse (two ahead, one each side)
TOWER_FRONT_WINDOWS_X = ((-1.75, -0.25), (0.25, 1.75))
TOWER_SIDE_WINDOW_Z = (18.0, 19.5)
# ventral keels under the hull: (z0, z1)
KEELS = ((10.0, 21.0), (-22.0, -6.0))
KEEL_DEPTH = 1.5

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
    for z in (-30.0, -20.0, 0.0, 20.0, 40.0):
        print("{%s, %.6f, %.6f}," % (z, half_width(z), half_height(z)))
