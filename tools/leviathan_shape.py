"""Shape and layout of the Sky Leviathan (sky_leviathan), shared by the model generator, the interior
grid and the texture.

MUST stay identical to LeviathanLayout (Java), which uses the same formulas and numbers for the
terrain probes, the seats and the autopilot (checked by LeviathanTest.matchesModelGenerator).

Ship-local coordinates, in blocks: x = lateral (+x = port), y = up (0 = the main deck of the
hanging ship), z = forward (+z = bow). Measured on the reference sheet (side view: 0.07 block per
pixel, see docs/LEVIATHAN_PLAN.md): 65 blocks from the nose spike to the tail spike, a balloon
52 x 24.4 x 19.6 (an egg-shaped body with elliptical, slightly flattened sections), a pirate
ship of 36 blocks (41 with the cutwater, 45 with the bowsprit) and 10 wide hanging 8 blocks under it.
"""
import math

CELL = 0.5

# ---------------------------------------------------------------- balloon
BALLOON_Y = 17.8          # axis of the balloon
BALLOON_Z = -0.6          # its middle
BALLOON_FRONT = 26.0      # nose at z = 25.4
BALLOON_REAR = 26.0       # tail end at z = -26.6
BALLOON_HW = 12.2         # half width (the sections are ellipses, wider than high)
BALLOON_HH = 9.8          # half height
BALLOON_FORE = (2.6, 0.55)   # scale = (1 - t^a)^b ahead of the middle: a blunt, rounded nose
BALLOON_AFT = (2.4, 0.6)   # a little more tapered behind it (egg shape)
NOSE_Z = BALLOON_Z + BALLOON_FRONT
TAIL_Z = BALLOON_Z - BALLOON_REAR
# wooden hoops round the balloon (z), the nose collar
HOOPS_Z = (21.0, 14.35, -17.15, -22.75)
NOSE_COLLAR_Z = 24.6
# big brown wooden panels on the sides, between the two middle hoops, from azimuth a0 to a1 (degrees
# from the top); a dark iron strap along their upper and lower edges
WOOD_Z = (HOOPS_Z[1], HOOPS_Z[2])
WOOD_AZ = (47.0, 142.0)
# nose fitting: the iron cone, the gear emblem, the spike
NOSE_GEAR_Z = NOSE_Z + 1.6
NOSE_GEAR_R = 1.9
NOSE_SPIKE_Z = 32.2
# tail: the iron end cap, the hub carrying the fins, the spike
HUB_Z = (TAIL_Z + 0.3, -30.0)
HUB_R = 1.25
TAIL_SPIKE_Z = -33.2
# observation deck on top of the balloon (flat, rounded ends), its flag mast
TOP_DECK_Y = 28.0
TOP_DECK_Z = (-14.0, 10.0)
TOP_DECK_HALF = 5.5
TOP_DECK_N = 3.0          # superellipse exponent of its plan
MAST_Z = 1.5
MAST_TOP = 36.8

# ---------------------------------------------------------------- the hanging ship
MAIN_DECK_Y = 0.0
HULL_HW = 5.0             # half beam
HULL_BOW_Z = 14.0         # the stem low down (a bluff, rounded bow; the long open head goes on beyond it)
HULL_STERN_Z = -19.8      # the transom
BOW_RAKE = 1.0            # the stem rakes forward: the bow reaches HULL_BOW_Z + BOW_RAKE at the forecastle
BOW_RAKE_Y = (-2.5, 3.0)  # from this height (where the bow ends at HULL_BOW_Z) to this one
BOW_PLAN = (14.4, 2.4, 0.5)     # plan: hw = HULL_HW * (1 - (z / s)^a)^b ahead of the middle
STERN_PLAN = (27.0, 2.6, 0.5)   # and behind it (a wide transom)
KEEL_Y = -6.3
# the keel line (z, y): a deep, rounded belly (lowest a little aft of the middle) curving up to the bow; aft, deep
# down to the sternpost (z -17.5), which rises almost straight, then the counter sweeping aft under the stern
# galleries to the transom (y -0.5); monotone cubic through these
KEEL_PTS = ((-19.8, -0.5), (-19.2, -0.9), (-18.5, -1.6), (-17.95, -2.7), (-17.7, -3.8), (-17.45, -4.9), (-17.0, -5.6),
            (-15.5, -6.0), (-10.0, -6.35), (-5.0, -6.55), (-1.0, -6.6), (3.0, -6.5), (6.0, -6.25), (9.0, -5.85), (11.0, -5.35),
            (12.6, -4.55), (13.5, -3.6), (14.0, -2.5))
# the run: aft of RUN[0], over RUN[1] blocks, the bilge's exponent drops by RUN[2] (finer, rounder lower stern)
RUN = (-16.6, 2.8, 1.3)
SHEER_WAIST = 1.0         # top of the hull planking in the waist (the bulwark)
TUMBLE = 0.025            # the castle sides lean in above the waist
SHELL = 0.4               # thickness of the hull planking (interior grid)
CUTWATER_TIP = (20.8, 1.2)       # (z, y) of the tip of the cutwater under the beakhead
BOW_GEAR = (21.8, 3.0, 1.2)      # (z, y, radius) of the gear wheel at the head of the beakhead (under the bowsprit)
BOWSPRIT = ((14.5, 2.6), (24.9, 5.3))  # (z, y) of its heel and its tip

# decks
FORECASTLE_Y = 3.0
FORECASTLE_Z = 9.0        # from here to the bow
QUARTERDECK_Y = 3.0
QUARTERDECK_Z = -7.5      # from here to the stern
POOP_Y = 5.5
POOP_Z = -15.0            # from here to the stern
RAIL_H = 1.1              # balustrades above the castle decks
DECK_SLAB = 0.5

# central tower from the main deck up to the balloon (ladder shaft inside), the big gear on it
TOWER_X = 1.5
TOWER_Z = (-3.0, 0.0)
SHAFT_X = 1.0
SHAFT_Z = (-2.5, -0.5)
TOWER_GEAR = (0.0, 4.5, 0.3, 1.5)   # centre height, how far its face stands off the side, radius  # (x, y, z of its face, radius): faces the bow

# helm on the quarterdeck, the pilot behind it facing the bow
HELM_Z = -10.75
PILOT_Z = -11.6
# ventral fin under the keel and the tail fins: (name, azimuth from the top (deg), z of the leading
# root, radial distance of the root from the axis (balloon fins) or y of the root (keel fin), span
# Lq, rake (deg, + sweeps the span backwards), root fraction of the outline)
FIN_CHORD = 0.85          # Lp = FIN_CHORD * Lq
FINS = (
    ("fin_dorsal", 0.0, -15.6, None, 5.9, 12.3),
    ("fin_upper_p", 30.0, -26.5, 1.6, 9.0, 4.6),
    ("fin_upper_s", -30.0, -26.5, 1.6, 9.0, 4.6),
    ("fin_side_p", 115.0, -26.5, 1.6, 10.0, 2.2),
    ("fin_side_s", -115.0, -26.5, 1.6, 10.0, 2.2),
    ("fin_lower", 180.0, -26.5, 1.6, 9.4, -12.0),
)
KEEL_FIN = ("fin_keel", 7.7, -5.9, 7.75, 16.9)   # name, z of the leading root, y of the root, Lq, rake
# outline of the bat-wing fins in (u, v) in [0, 1]^2 (u along the chord, backwards; v along the span)
FIN_ROOT_U = 0.32          # the root runs from u = 0 to this
KEEL_FIN_ROOT_U = 0.72     # the keel fin has a long root (a shark's dorsal fin)
FIN_TIP = (0.92, 1.0)
FIN_RIBS = (0.2, 0.42, 0.64, 0.84)   # rib tips along the trailing edge (fraction from the tip)
FIN_HOLES = (0.74, 0.82, 0.9)        # three round holes along the leading edge near the tip
FIN_HOLE_R = 0.032


def balloon_scale(z):
    t = (z - BALLOON_Z) / (BALLOON_FRONT if z >= BALLOON_Z else BALLOON_REAR)
    a, b = BALLOON_FORE if t >= 0 else BALLOON_AFT
    t = abs(t)
    if t >= 1.0:
        return 0.0
    return (1.0 - t ** a) ** b


def balloon_hw(z):
    return BALLOON_HW * balloon_scale(z)


def balloon_hh(z):
    return BALLOON_HH * balloon_scale(z)


def balloon_point(z, az_deg, out=0.0):
    """Point of the balloon surface at z, azimuth (degrees from the top, + towards port), pushed out
    along the normal of the section by `out`."""
    a = math.radians(az_deg)
    w, h = balloon_hw(z), balloon_hh(z)
    x, y = math.sin(a) * w, math.cos(a) * h
    if out:
        nx, ny = x / max(w, 1e-6) ** 2, y / max(h, 1e-6) ** 2
        n = math.hypot(nx, ny)
        if n > 1e-9:
            x, y = x + nx / n * out, y + ny / n * out
    return (x, BALLOON_Y + y, z)


def inside_balloon(x, y, z, inset=0.0):
    w, h = balloon_hw(z) - inset, balloon_hh(z) - inset
    if w <= 0 or h <= 0:
        return False
    return (x / w) ** 2 + ((y - BALLOON_Y) / h) ** 2 <= 1.0


def top_deck_half(z):
    """Half width of the observation deck at z (0 outside it)."""
    z0, z1 = TOP_DECK_Z
    zc, hl = (z0 + z1) / 2, (z1 - z0) / 2
    t = abs(z - zc) / hl
    if t >= 1.0:
        return 0.0
    return TOP_DECK_HALF * (1.0 - t ** TOP_DECK_N) ** (1.0 / TOP_DECK_N)


# ---------------------------------------------------------------- hull
def hull_hw(z):
    """Half beam at z (at the widest of the section)."""
    s, a, b = BOW_PLAN if z >= 0 else STERN_PLAN
    t = abs(z) / s
    if z > HULL_BOW_Z or z < HULL_STERN_Z or t >= 1.0:
        return 0.0
    return HULL_HW * (1.0 - t ** a) ** b


def _keel_slopes():
    p = KEEL_PTS
    n = len(p)
    d = [(p[i + 1][1] - p[i][1]) / (p[i + 1][0] - p[i][0]) for i in range(n - 1)]
    m = [d[0]] + [0.0 if d[i - 1] * d[i] <= 0 else (d[i - 1] + d[i]) / 2 for i in range(1, n - 1)] + [d[-1]]
    for i in range(n - 1):   # Fritsch-Carlson: no overshoot
        if d[i] == 0:
            m[i] = m[i + 1] = 0.0
            continue
        a, b = m[i] / d[i], m[i + 1] / d[i]
        s = a * a + b * b
        if s > 9:
            t = 3 / math.sqrt(s)
            m[i], m[i + 1] = t * a * d[i], t * b * d[i]
    return m


KEEL_SLOPES = _keel_slopes()


def keel_y(z):
    """Bottom of the hull (outside of the keel planking) at z."""
    p, m = KEEL_PTS, KEEL_SLOPES
    if z <= p[0][0]:
        return p[0][1]
    if z >= p[-1][0]:
        return p[-1][1]
    i = 0
    while z > p[i + 1][0]:
        i += 1
    h = p[i + 1][0] - p[i][0]
    t = (z - p[i][0]) / h
    h00, h10, h01, h11 = 2 * t ** 3 - 3 * t ** 2 + 1, t ** 3 - 2 * t ** 2 + t, -2 * t ** 3 + 3 * t ** 2, t ** 3 - t ** 2
    return h00 * p[i][1] + h10 * h * m[i] + h01 * p[i + 1][1] + h11 * h * m[i + 1]


def deck_y(z):
    """Walkable deck at z (main deck, forecastle, quarterdeck, poop)."""
    if z >= FORECASTLE_Z:
        return FORECASTLE_Y
    if z <= POOP_Z:
        return POOP_Y
    if z <= QUARTERDECK_Z:
        return QUARTERDECK_Y
    return MAIN_DECK_Y


def _smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def sheer_y(z):
    """Top of the hull planking: the waist bulwark, the castle decks (their balustrades are above),
    the walls of the chart room under the poop; smooth curved steps between them."""
    y = SHEER_WAIST
    y += (FORECASTLE_Y - SHEER_WAIST) * _smooth((z - (FORECASTLE_Z - 1.2)) / 1.2)
    y += (QUARTERDECK_Y - SHEER_WAIST) * _smooth(((QUARTERDECK_Z + 1.2) - z) / 1.2)
    y += (POOP_Y - QUARTERDECK_Y) * _smooth(((POOP_Z + 1.0) - z) / 1.0)
    return y


def section_eta(z, y):
    k = keel_y(z)
    return (y - k) / (SHEER_WAIST - k)


def bow_end(y):
    """z of the stem at height y (raked forwards)."""
    y0, y1 = BOW_RAKE_Y
    return HULL_BOW_Z + BOW_RAKE * min(1.0, max(0.0, (y - y0) / (y1 - y0)))


def hull_x(z, y):
    """Half width of the outside of the hull at (z, y): rounded bilge, then a slight tumblehome above
    the waist (castles); the bow's plan is stretched forwards with the height (raked stem)."""
    if z > 0:
        e = bow_end(y)
        if z >= e:
            return 0.0
        w = hull_hw(z * HULL_BOW_Z / e)
    else:
        w = hull_hw(z)
    if w <= 0:
        return 0.0
    k = keel_y(z)
    if y < k:
        return 0.0
    if y <= SHEER_WAIST:
        eta = (y - k) / (SHEER_WAIST - k)
        p = 3.0 - RUN[2] * _smooth((RUN[0] - z) / RUN[1])
        return w * (0.12 + 0.88 * (1.0 - (1.0 - eta) ** p) ** 0.5)
    return w * (1.0 - TUMBLE * (y - SHEER_WAIST))


# the stern: curved in plan (it bulges aft by STERN_RAKE[0] in the middle) and, from y STERN_RAKE[2] up over
# STERN_RAKE[3] blocks, more and more overhanging (STERN_RAKE[1] at the poop deck): the upper stern over the
# galleries, the poop deck running on over it (visual, and in the grid a slab and its taffrail)
STERN_RAKE = (0.3, 1.65, 2.4, 3.1)


def stern_bulge(y):
    a, b, y0, dy = STERN_RAKE
    return a + (b - a) * _smooth((y - y0) / dy)


def stern_z(x, y):
    """z of the aft face of the stern at (x, y): -> HULL_STERN_Z at the sides (where it meets the hull's sides)."""
    w = hull_x(HULL_STERN_Z, min(y, POOP_Y))
    if w <= 1e-6:
        return HULL_STERN_Z
    u = min(1.0, abs(x) / w)
    return HULL_STERN_Z - stern_bulge(y) * (1.0 - u ** 4) ** 0.25


def inside_hull(x, y, z, inset=0.0):
    """Inside the hull planking (shrunk by inset), below its sheer."""
    if y > sheer_y(z) or y < keel_y(z) + inset:
        return False
    return abs(x) <= hull_x(z, y) - inset


# ---------------------------------------------------------------- fins
def _bezier2(p0, p1, p2, t):
    return tuple((1 - t) ** 2 * a + 2 * t * (1 - t) * b + t * t * c for a, b, c in zip(p0, p1, p2))


def fin_outline(root_u=FIN_ROOT_U, n=24):
    """Polygon of the bat-wing fin in (u, v): the root along v = 0, the convex leading edge up to the
    tip, the scalloped trailing edge (rib tips sticking out, hollows between them) back to the root."""
    tip = FIN_TIP
    lead = [_bezier2((0.0, 0.0), (0.06, 0.78), tip, j / n) for j in range(n + 1)]
    tail_end = (root_u, 0.0)
    pts = list(lead)
    # trailing edge, from the tip back to the end of the root
    dx, dy = tail_end[0] - tip[0], tail_end[1] - tip[1]
    L = math.hypot(dx, dy)
    ox, oy = dy / L, -dx / L        # outward normal (away from the leading edge)
    if ox * (tip[0] - 0.0) + oy * 0 < 0:
        ox, oy = -ox, -oy
    marks = [0.0] + list(FIN_RIBS) + [1.0]
    for i in range(len(marks) - 1):
        f0, f1 = marks[i], marks[i + 1]
        for j in range(1, 9):
            f = f0 + (f1 - f0) * j / 8
            s = j / 8
            # a hollow between two rib tips; each rib tip juts out a little
            dip = -0.05 * math.sin(math.pi * s) * (1.0 if 0 < i < len(marks) - 1 or f1 < 1.0 else 0.5)
            jut = 0.025 if (j == 8 and i < len(marks) - 2) else 0.0
            off = dip + jut
            pts.append((tip[0] + dx * f + ox * off, tip[1] + dy * f + oy * off))
    pts.append((0.0, 0.0))
    return pts


def fin_ribs(root_u=FIN_ROOT_U):
    """Ribs of a fin in (u, v): from a point near the root to the tip and to each rib tip."""
    tip = FIN_TIP
    dx, dy = root_u - tip[0], -tip[1]
    L = math.hypot(dx, dy)
    ox, oy = dy / L, -dx / L
    if ox < 0:
        ox, oy = -ox, -oy
    base = (root_u * 0.35, 0.0)
    out = [(base, tip)]
    for f in FIN_RIBS:
        out.append((base, (tip[0] + dx * f + ox * 0.025, tip[1] + dy * f + oy * 0.025)))
    return out


def fin_holes():
    """Centres of the three holes near the tip (u, v), just inside the leading edge."""
    out = []
    for t in FIN_HOLES:
        p = _bezier2((0.0, 0.0), (0.06, 0.78), FIN_TIP, t)
        q = _bezier2((0.0, 0.0), (0.06, 0.78), FIN_TIP, t + 0.01)
        tx, ty = q[0] - p[0], q[1] - p[1]
        L = math.hypot(tx, ty)
        nx, ny = ty / L, -tx / L        # into the fin (to the right of the leading edge going up)
        out.append((p[0] + nx * 0.07, p[1] + ny * 0.07))
    return out


def point_in_poly(x, y, poly):
    inside = False
    n = len(poly)
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi:
            inside = not inside
        j = i
    return inside


def fin_inside(u, v, root_u=FIN_ROOT_U, poly=None, holes=True):
    poly = poly or fin_outline(root_u)
    if not point_in_poly(u, v, poly):
        return False
    if holes and root_u == FIN_ROOT_U:
        for hx, hy in fin_holes():
            if (u - hx) ** 2 + ((v - hy) * FIN_CHORD) ** 2 < FIN_HOLE_R ** 2:
                return False
    return True


def fin_frame(fin):
    """Origin (leading root), chord axis (backwards), span axis, normal, Lp, Lq of a tail fin."""
    name, az, z0, r0, lq, rake = fin
    a = math.radians(az)
    rad = (math.sin(a), math.cos(a), 0.0)
    if r0 is None:   # on the balloon surface
        x, y, z = balloon_point(z0, az, -0.15)
        origin = (x, y, z)
    else:
        origin = (rad[0] * r0, BALLOON_Y + rad[1] * r0, z0)
    back = (0.0, 0.0, -1.0)
    k = math.radians(rake)
    span = tuple(math.cos(k) * r + math.sin(k) * b for r, b in zip(rad, back))
    chord = tuple(math.cos(k) * b - math.sin(k) * r for r, b in zip(rad, back))
    normal = (chord[1] * span[2] - chord[2] * span[1], chord[2] * span[0] - chord[0] * span[2], chord[0] * span[1] - chord[1] * span[0])
    return origin, chord, span, normal, FIN_CHORD * lq, lq


def keel_fin_frame():
    name, z0, y0, lq, rake = KEEL_FIN
    k = math.radians(rake)
    span = (0.0, -math.cos(k), -math.sin(k))
    chord = (0.0, math.sin(k), -math.cos(k))
    normal = (1.0, 0.0, 0.0)
    return (0.0, y0, z0), chord, span, normal, FIN_CHORD * lq, lq


def fin_point(frame, u, v):
    o, c, s, n, lp, lq = frame
    return tuple(o[i] + c[i] * u * lp + s[i] * v * lq for i in range(3))


if __name__ == "__main__":
    # values checked by LeviathanTest.matchesModelGenerator
    for z in (-24.0, -12.0, -0.6, 10.0, 22.0):
        print("{%s, %.6f, %.6f}," % (z, balloon_hw(z), balloon_hh(z)))
    for z, y in ((-18.0, -2.0), (-10.0, -4.0), (0.0, -5.5), (0.0, 0.5), (8.0, -3.0), (13.0, 2.0), (-16.5, 4.5), (14.5, 2.5)):
        print("{%s, %s, %.6f, %.6f, %.6f}," % (z, y, hull_x(z, y), keel_y(z), sheer_y(z)))
    for f in FINS:
        print("{%s}, // %s" % (", ".join("%.6f" % c for c in fin_point(fin_frame(f), *FIN_TIP)), f[0]))
    print("{%s}, // keel fin" % ", ".join("%.6f" % c for c in fin_point(keel_fin_frame(), *FIN_TIP)))
