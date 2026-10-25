"""Furniture made for the Sky Leviathan (what the decoration mods do not have, or not close enough to the
reference sheet's interior views): the timber framing of the rooms (posts, ceiling beams), iron-bound
sea chests, upright barrels, coils of rope, the dark red blanket laid on the mods' double bed, wall
brackets for the mods' lanterns, the windows and portholes seen from inside, the navigator's
instruments (compass, sextant, dividers, rolled charts, hourglass, inkwell), shelves of jars and
bottles, the engine room's riveted boiler, pressure tanks, pipes, valves, gauges, levers, gears and
catwalk railings, a coal heap, candles.

Every function takes the bone, a name and its placement (ship-local blocks: +x port, +y up, +z bow).
Cube names start with "lit_" (lit by the airship's lamps in the rooms) or "glow_" (full bright).
Regions "in_*" are in the interior texture (tools/leviathan_texture.REGIONS_IN), the others in the
main texture.
"""
import math

import numpy as np

import generate_galley as gg
import generate_airship as ga

v3, norm, add_cube, beam = gg.v3, gg.norm, gg.add_cube, gg.beam
EYE = np.eye(3)
prism, disc, dial, ring = ga.prism, ga.disc, ga.dial, ga.ring


def tube(bone, name, p0, p1, d, region, sides=6, **kw):
    return ga.tube(bone, name, p0, p1, d, region, sides=sides, **kw)


def ry(a):
    return gg.ry(a)


def frame(normal):
    """Axes (u along the wall, up, n out of the wall) of a part on a wall facing `normal` (horizontal)."""
    n = norm(v3(normal[0], 0, normal[2]))
    u = np.cross(v3(0, 1, 0), n)
    return np.column_stack([u, v3(0, 1, 0), n]), u, n


def box(bone, name, c, size, region, R=EYE, **kw):
    return add_cube(bone, name, v3(*c), R, size, region, **kw)


YAW = {"bow": 0.0, "port": math.pi / 2, "stern": math.pi, "starboard": -math.pi / 2}


def yaw_r(facing):
    """Rotation of an object whose front looks along +z (bow) turned to face `facing` (name or radians)."""
    return ry(YAW[facing] if isinstance(facing, str) else facing)


# ---------------------------------------------------------------- timber framing of the rooms
def timber(bone, name, a, b, w=0.24, d=None, region="in_beam"):
    """A squared timber (post, beam, knee) from a to b."""
    a, b = v3(*a), v3(*b)
    up = v3(0, 1, 0) if abs(norm(b - a)[1]) < 0.9 else v3(1, 0, 0)
    beam(bone, "lit_" + name, a, b, w, region, width=d or w, up=up)


def knee(bone, name, corner, along, down, s=0.45, w=0.16):
    """A diagonal brace under a beam, from the post to the beam."""
    c = v3(*corner)
    timber(bone, name, c + v3(*down) * s, c + v3(*along) * s, w=w)


# ---------------------------------------------------------------- storage
def sea_chest(bone, name, p, facing="bow", w=0.95, d=0.6, h=0.62, region="in_chest"):
    """An iron-bound sea chest with a rounded lid, a brass lock plate and side handles."""
    R = yaw_r(facing)
    p = v3(*p)
    hb = h * 0.66
    box(bone, "lit_%s_body" % name, p + v3(0, hb / 2, 0), (w, hb, d), {"all": region, "+2": "in_chest_lid"}, R=R, u_dir=R @ v3(1, 0, 0))
    lid_h = h - hb
    box(bone, "lit_%s_lid" % name, p + v3(0, hb + lid_h * 0.35, 0), (w + 0.03, lid_h * 0.7, d + 0.03), "in_chest_lid", R=R,
        u_dir=R @ v3(1, 0, 0))
    box(bone, "lit_%s_lid_top" % name, p + v3(0, hb + lid_h * 0.82, 0), (w + 0.02, lid_h * 0.36, d * 0.7), "in_chest_lid", R=R,
        u_dir=R @ v3(1, 0, 0))
    for k, x in enumerate((-w * 0.3, w * 0.3)):
        box(bone, "lit_%s_band%d" % (name, k), p + R @ v3(x, h * 0.5, 0), (0.07, h + 0.02, d + 0.05), "in_iron", R=R)
        box(bone, "lit_%s_band_top%d" % (name, k), p + R @ v3(x, h - lid_h * 0.15, 0), (0.07, 0.05, d * 0.72), "in_iron", R=R)
    box(bone, "lit_%s_lock" % name, p + R @ v3(0, hb, d / 2 + 0.02), (0.14, 0.18, 0.03), "in_brass", R=R)
    for e in (-1, 1):
        box(bone, "lit_%s_handle%d" % (name, e > 0), p + R @ v3(e * (w / 2 + 0.03), hb * 0.75, 0), (0.04, 0.06, 0.22), "in_iron", R=R)


def barrel(bone, name, p, r=0.36, h=0.95, lid=True):
    """An upright barrel: bulging staves (three bands of a regular prism), iron hoops, a lid."""
    p = v3(*p)
    up = v3(0, 1, 0)
    e1 = v3(1, 0, 0)
    for k, (y0, y1, rr) in enumerate(((0.0, 0.3, 0.9), (0.3, 0.65, 1.0), (0.65, 0.95, 0.9))):
        prism(bone, "lit_%s_staves%d" % (name, k), p + up * (h * (y0 + y1) / 2), up, e1, h * (y1 - y0), r * rr, 10, "in_staves",
              phase=0.1 * k)
    for k, (y, rr) in enumerate(((0.12, 0.93), (0.36, 1.02), (0.64, 1.02), (0.86, 0.93))):
        prism(bone, "lit_%s_hoop%d" % (name, k), p + up * (h * y), up, e1, 0.06, r * rr + 0.025, 10, "in_iron", phase=0.05)
    if lid:
        disc(bone, "lit_%s_lid" % name, p + up * (h * 0.95 - 0.02), up, r * 0.86, 0.04, "in_barrel_lid", sides=10)


def cask(bone, name, p, facing=(0, 0, -1), r=0.34, l=0.85, tap=True):
    """A cask lying on its wooden cradle, its lid (and its brass tap) turned towards `facing` (horizontal):
    p is the centre of the cradle on the floor."""
    p = v3(*p)
    n = norm(v3(facing[0], 0, facing[2]))
    up = v3(0, 1, 0)
    side = np.cross(up, n)
    yc = 0.16 + r
    c = p + up * yc
    # the cradle: two saddles across the cask, two rails along it
    R = np.column_stack([side, up, n])
    for e in (-1, 1):
        box(bone, "lit_%s_saddle%d" % (name, e > 0), p + n * (e * l * 0.3) + up * 0.12, (2 * r * 0.95, 0.24, 0.12), "in_beam", R=R)
        box(bone, "lit_%s_rail%d" % (name, e > 0), p + side * (e * r * 0.7) + up * 0.04, (0.1, 0.08, l * 0.85), "in_beam", R=R)
    # the staves (bulging in the middle), the hoops, the two heads
    base = c - n * (l / 2)
    for k, (a, b, rr) in enumerate(((0.0, 0.3, 0.9), (0.3, 0.7, 1.0), (0.7, 1.0, 0.9))):
        prism(bone, "lit_%s_staves%d" % (name, k), base + n * (l * (a + b) / 2), n, up, l * (b - a), r * rr, 10, "in_staves", phase=0.1 * k)
    for k, (t, rr) in enumerate(((0.1, 0.93), (0.34, 1.02), (0.66, 1.02), (0.9, 0.93))):
        prism(bone, "lit_%s_hoop%d" % (name, k), base + n * (l * t), n, up, 0.06, r * rr + 0.025, 10, "in_iron", phase=0.05)
    disc(bone, "lit_%s_lid" % name, base + n * (l + 0.01), n, r * 0.86, 0.04, "in_barrel_lid", sides=10)
    disc(bone, "lit_%s_back" % name, base - n * 0.01, n, r * 0.86, 0.04, "in_barrel_lid", sides=10)
    if tap:
        t0 = base + n * (l + 0.03) - up * (r * 0.45)
        tube(bone, "lit_%s_tap" % name, t0, t0 + n * 0.12, 0.06, "in_brass")
        box(bone, "lit_%s_tap_spout" % name, t0 + n * 0.12 - up * 0.04, (0.05, 0.1, 0.05), "in_brass", R=R)
        box(bone, "lit_%s_tap_key" % name, t0 + n * 0.09 + up * 0.05, (0.12, 0.03, 0.03), "in_brass", R=R)


def rope_coil(bone, name, p, r=0.32, turns=3, th=0.09):
    """A coil of rope lying on the deck."""
    p = v3(*p)
    for k in range(turns):
        rr = r * (1.0 - 0.18 * k)
        ring(bone, "lit_%s_%d" % (name, k), p + v3(0, th * (0.5 + 0.9 * k), 0), (0, 1, 0), rr, th, "in_rope", n=8, phase=0.3 * k)


def sack(bone, name, p, yaw=0.0, s=1.0):
    """A plump sack of flour or grain, tied at the top."""
    p = v3(*p)
    R = ry(yaw)
    box(bone, "lit_%s_body" % name, p + v3(0, 0.28 * s, 0), (0.55 * s, 0.56 * s, 0.42 * s), "in_sack", R=R)
    box(bone, "lit_%s_top" % name, p + v3(0, 0.6 * s, 0), (0.32 * s, 0.12 * s, 0.26 * s), "in_sack", R=R)
    box(bone, "lit_%s_tie" % name, p + v3(0, 0.69 * s, 0), (0.14 * s, 0.08 * s, 0.14 * s), "in_rope", R=R)


def coal_heap(bone, name, p, r=0.6):
    p = v3(*p)
    for k, (dx, dz, s) in enumerate(((0, 0, 1.0), (0.3, 0.2, 0.7), (-0.3, 0.15, 0.65), (0.1, -0.3, 0.6), (-0.2, -0.25, 0.5))):
        hh = 0.28 * s
        box(bone, "lit_%s_%d" % (name, k), p + v3(dx * r, hh / 2, dz * r), (r * s, hh, r * s * 0.9), "in_coal", R=ry(0.4 * k))


# ---------------------------------------------------------------- bedding, cloth, rugs
def bed_blanket(bone, name, x, y, z, yaw_deg, xc=0.0, half=15.4):
    """The dark red blanket laid over the mods' double bed (farmhouse_decorations:double_bed, placed at
    (x, y, z) with InteriorDecor yaw `yaw_deg`): it covers the bed's own sheets from the foot to the
    pillows and hangs over its sides (bed model: x -15..15 px, top of the sheets 7.75 px, z 1.75..20.5).
    The single bed: xc=8, half=8.9 (its model: x 0..16 px, the same height and length)."""
    a = math.radians(yaw_deg)
    c, s = math.cos(a), math.sin(a)

    def P(px_, py_, pz_):
        qx, qz = px_ - 0.5, pz_ - 0.5
        return v3(x + qx * c + qz * s, y + py_, z - qx * s + qz * c)
    R = np.column_stack([v3(c, 0, -s), v3(0, 1, 0), v3(s, 0, c)])
    z0, z1 = 1.4 / 16, 21.0 / 16
    xm = xc / 16
    wt = (2 * half + 0.2) / 16
    top = P(xm, 0.0, (z0 + z1) / 2)
    box(bone, "lit_%s_top" % name, top + v3(0, 8.0 / 16, 0), (wt, 0.05, z1 - z0), {"all": "in_blanket", "+2": "in_blanket"}, R=R,
        stretch=True)
    for e in (-1, 1):
        side = P(xm + e * half / 16, 0.0, (z0 + z1) / 2)
        box(bone, "lit_%s_side%d" % (name, e > 0), side + v3(0, 6.6 / 16, 0), (0.05, 2.9 / 16, z1 - z0), "in_blanket", R=R, stretch=True)
    foot = P(xm, 0.0, z0 - 0.02)
    box(bone, "lit_%s_foot" % name, foot + v3(0, 6.6 / 16, 0), (wt, 2.9 / 16, 0.05), "in_blanket", R=R, stretch=True)
    # the folded-back sheet at the head of the blanket
    fold = P(xm, 0.0, z1 + 0.06)
    box(bone, "lit_%s_fold" % name, fold + v3(0, 8.1 / 16, 0), (wt - 1.0 / 16, 0.06, 0.16), "in_bedding", R=R)


def rug(bone, name, p, w, l, region="in_rug", yaw=0.0):
    p = v3(*p)
    add_cube(bone, "lit_" + name, p + v3(0, 0.012, 0), ry(yaw), (w, 0.02, l), {"all": None, "+2": region}, stretch=True,
             u_dir=ry(yaw) @ v3(1, 0, 0), v_dir=ry(yaw) @ v3(0, 0, 1))


def cushion(bone, name, p, w=0.4, d=0.4):
    box(bone, "lit_" + name, v3(*p) + v3(0, 0.04, 0), (w, 0.08, d), "in_cushion")


# ---------------------------------------------------------------- lights and windows
def wall_bracket(bone, name, p, normal, arm=0.34):
    """An iron bracket on a wall (p on the wall, at the height of the arm): returns the point under the
    arm's tip where a lantern hangs (its top)."""
    R, u, n = frame(normal)
    p = v3(*p)
    box(bone, "lit_%s_plate" % name, p + n * 0.02, (0.12, 0.3, 0.04), "in_iron", R=R)
    tip = p + n * arm
    beam(bone, "lit_%s_arm" % name, p + n * 0.02 + v3(0, 0.08, 0), tip + v3(0, 0.08, 0), 0.05, "in_iron")
    beam(bone, "lit_%s_brace" % name, p + n * 0.02 - v3(0, 0.12, 0), p + n * arm * 0.6 + v3(0, 0.08, 0), 0.04, "in_iron")
    box(bone, "lit_%s_hook" % name, tip + v3(0, 0.02, 0), (0.03, 0.1, 0.03), "in_iron")
    return tip - v3(0, 0.03, 0)


def candle(bone, name, p, h=0.18):
    p = v3(*p)
    box(bone, "lit_%s_dish" % name, p + v3(0, 0.015, 0), (0.14, 0.03, 0.14), "in_brass")
    box(bone, "lit_%s_wax" % name, p + v3(0, 0.03 + h / 2, 0), (0.05, h, 0.05), "in_candle")
    box(bone, "glow_%s_flame" % name, p + v3(0, 0.05 + h, 0), (0.03, 0.06, 0.03), "in_glow")


def window_in(bone, name, center, normal, w=0.85, h=1.1):
    """A leaded window seen from inside (daylight through blue diamond panes), its frame and sill."""
    R, u, n = frame(normal)
    c = v3(*center)
    add_cube(bone, "glow_%s" % name, c + n * 0.03, R, (w, h, 0.02), {"all": None, "+3": "in_window", "-3": "in_window"}, stretch=True,
             u_dir=u, v_dir=v3(0, -1, 0))
    for e in (-1, 1):
        box(bone, "lit_%s_jamb%d" % (name, e > 0), c + u * e * (w / 2 + 0.05) + n * 0.06, (0.12, h + 0.16, 0.1), "in_beam", R=R)
    box(bone, "lit_%s_sill" % name, c - v3(0, h / 2 + 0.06, 0) + n * 0.1, (w + 0.34, 0.08, 0.2), "in_beam", R=R)
    box(bone, "lit_%s_head" % name, c + v3(0, h / 2 + 0.07, 0) + n * 0.06, (w + 0.3, 0.12, 0.12), "in_beam", R=R)


def porthole_in(bone, name, center, normal, r=0.26):
    """A round porthole seen from inside: brass rim with its dogs, sky-blue glass."""
    R, u, n = frame(normal)
    c = v3(*center)
    add_cube(bone, "glow_%s" % name, c + n * 0.02, R, (2 * r, 2 * r, 0.02), {"all": None, "+3": "in_porthole", "-3": "in_porthole"},
             stretch=True, u_dir=u, v_dir=v3(0, -1, 0))
    ring(bone, "lit_%s_rim" % name, c + n * 0.04, n, r + 0.02, 0.07, "in_brass", n=10)
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        d = u * math.cos(a) + v3(0, 1, 0) * math.sin(a)
        box(bone, "lit_%s_dog%d" % (name, k), c + d * (r + 0.1) + n * 0.05, (0.06, 0.06, 0.06), "in_brass", R=R)


def painting_frame(bone, name, center, normal, w, h, region="in_beam"):
    """A dark wooden frame round a vanilla painting (drawn by the renderer)."""
    R, u, n = frame(normal)
    c = v3(*center)
    box(bone, "lit_%s_back" % name, c + n * 0.02, (w + 0.04, h + 0.04, 0.04), "in_beam", R=R)
    for e in (-1, 1):
        box(bone, "lit_%s_v%d" % (name, e > 0), c + u * e * (w / 2 + 0.05) + n * 0.05, (0.1, h + 0.2, 0.06), region, R=R)
        box(bone, "lit_%s_h%d" % (name, e > 0), c + v3(0, e * (h / 2 + 0.05), 0) + n * 0.05, (w + 0.2, 0.1, 0.06), region, R=R)


def wall_map(bone, name, center, normal, w=1.4, h=0.95):
    R, u, n = frame(normal)
    c = v3(*center)
    add_cube(bone, "lit_%s" % name, c + n * 0.02, R, (w, h, 0.02), {"all": None, "+3": "in_map_wall"}, stretch=True, u_dir=u, v_dir=v3(0, -1, 0))
    for k, (dx, dy) in enumerate(((-1, 1), (1, 1), (-1, -1), (1, -1))):
        box(bone, "lit_%s_pin%d" % (name, k), c + u * dx * (w / 2 - 0.06) + v3(0, dy * (h / 2 - 0.06), 0) + n * 0.04, (0.04, 0.04, 0.03),
            "in_brass", R=R)


# ---------------------------------------------------------------- navigator's instruments
def compass(bone, name, p):
    p = v3(*p)
    disc(bone, "lit_%s_box" % name, p + v3(0, 0.03, 0), (0, 1, 0), 0.13, 0.06, "in_brass", sides=8)
    add_cube(bone, "lit_%s_face" % name, p + v3(0, 0.065, 0), EYE, (0.2, 0.01, 0.2), {"all": None, "+2": "in_gauge"}, stretch=True)


def sextant(bone, name, p, yaw=0.3):
    p = v3(*p)
    R = ry(yaw)
    for k in range(4):
        a0, a1 = math.radians(-30 + 15 * k), math.radians(-15 + 15 * k)
        q0 = p + R @ v3(math.sin(a0) * 0.22, 0.012, -math.cos(a0) * 0.22 + 0.11)
        q1 = p + R @ v3(math.sin(a1) * 0.22, 0.012, -math.cos(a1) * 0.22 + 0.11)
        beam(bone, "lit_%s_arc%d" % (name, k), q0, q1, 0.02, "in_brass", width=0.03)
    beam(bone, "lit_%s_arm" % name, p + R @ v3(0, 0.02, 0.11), p + R @ v3(0.05, 0.02, -0.11), 0.02, "in_brass", width=0.03)
    beam(bone, "lit_%s_frame_a" % name, p + R @ v3(0, 0.015, 0.11), p + R @ v3(-0.11, 0.015, -0.08), 0.02, "in_brass", width=0.025)
    beam(bone, "lit_%s_frame_b" % name, p + R @ v3(0, 0.015, 0.11), p + R @ v3(0.11, 0.015, -0.08), 0.02, "in_brass", width=0.025)


def dividers(bone, name, p, yaw=0.0):
    p = v3(*p)
    R = ry(yaw)
    for e in (-1, 1):
        beam(bone, "lit_%s_leg%d" % (name, e > 0), p + R @ v3(0, 0.01, -0.1), p + R @ v3(e * 0.05, 0.01, 0.1), 0.012, "in_brass", width=0.018)


def map_roll(bone, name, p, yaw=0.0, l=0.6, r=0.05):
    p = v3(*p)
    d = ry(yaw) @ v3(1, 0, 0)
    tube(bone, "lit_%s" % name, p + v3(0, r, 0) - d * l / 2, p + v3(0, r, 0) + d * l / 2, 2 * r, "in_paper", sides=6)
    tube(bone, "lit_%s_tie" % name, p + v3(0, r, 0) - d * 0.03, p + v3(0, r, 0) + d * 0.03, 2 * r + 0.02, "in_red_cloth", sides=6)


def chart_sheet(bone, name, p, yaw=0.2, w=0.8, l=0.6):
    add_cube(bone, "lit_" + name, v3(*p) + v3(0, 0.008, 0), ry(yaw), (w, 0.012, l), {"all": None, "+2": "in_chart"}, stretch=True)


def inkwell(bone, name, p):
    p = v3(*p)
    box(bone, "lit_%s_pot" % name, p + v3(0, 0.04, 0), (0.08, 0.08, 0.08), "in_slate")
    beam(bone, "lit_%s_quill" % name, p + v3(0.0, 0.07, 0.0), p + v3(0.08, 0.3, 0.05), 0.02, "in_paper", width=0.05)


def hourglass(bone, name, p):
    p = v3(*p)
    for k, y in enumerate((0.01, 0.25)):
        box(bone, "lit_%s_plate%d" % (name, k), p + v3(0, y, 0), (0.14, 0.02, 0.14), "in_beam")
    for k, (dx, dz) in enumerate(((1, 1), (1, -1), (-1, 1), (-1, -1))):
        box(bone, "lit_%s_post%d" % (name, k), p + v3(dx * 0.055, 0.13, dz * 0.055), (0.015, 0.24, 0.015), "in_beam")
    for k, (y, s) in enumerate(((0.07, 0.09), (0.19, 0.09))):
        box(bone, "lit_%s_bulb%d" % (name, k), p + v3(0, y, 0), (s, 0.1, s), "in_paper")


# ---------------------------------------------------------------- shelves
def jar_shelf(bone, name, p, normal, w=1.0, h=1.6, rows=3, d=0.34):
    """A wooden shelf unit against a wall, its shelves lined with jars, bottles and crocks
    (p = middle of its foot against the wall)."""
    R, u, n = frame(normal)
    p = v3(*p)
    for e in (-1, 1):
        box(bone, "lit_%s_side%d" % (name, e > 0), p + u * e * (w / 2 - 0.04) + v3(0, h / 2, 0) + n * d / 2, (0.08, h, d), "in_plank", R=R)
    box(bone, "lit_%s_back" % name, p + v3(0, h / 2, 0) + n * 0.02, (w, h, 0.04), "in_beam", R=R)
    gap = (h - 0.1) / rows
    for k in range(rows + 1):
        y = 0.05 + gap * k
        box(bone, "lit_%s_board%d" % (name, k), p + v3(0, y, 0) + n * d / 2, (w - 0.08, 0.05, d), "in_plank", R=R)
        if k < rows:
            add_cube(bone, "lit_%s_jars%d" % (name, k), p + v3(0, y + gap * 0.42, 0) + n * (d * 0.55), R, (w - 0.12, gap * 0.8, 0.02),
                     {"all": None, "+3": "in_jars" if k % 2 == 0 else "in_jars2"}, stretch=True, u_dir=u, v_dir=v3(0, -1, 0))


def book_shelf(bone, name, p, normal, w=1.0, h=1.0, d=0.3):
    """A small hanging bookshelf (two rows of books)."""
    R, u, n = frame(normal)
    p = v3(*p)
    add_cube(bone, "lit_%s" % name, p + v3(0, h / 2, 0) + n * d / 2, R, (w, h, d), {"all": "in_plank", "+3": "in_books"}, stretch=True,
             u_dir=u, v_dir=v3(0, -1, 0))


# ---------------------------------------------------------------- engine room
def gear(bone, name, c, axis, r, th, teeth=12, region="in_brass", spokes=6, rim="in_brass", hub="in_iron"):
    """A gear wheel: a rim, square teeth, spokes, a hub."""
    axis = norm(v3(*axis))
    c = v3(*c)
    ring(bone, name + "_rim", c, axis, r * 0.84, th, rim, n=max(10, teeth))
    e1 = norm(np.cross(axis, v3(0, 1, 0) if abs(axis[1]) < 0.9 else v3(1, 0, 0)))
    e2 = np.cross(axis, e1)
    for k in range(teeth):
        a = 2 * math.pi * (k + 0.5) / teeth
        d = e1 * math.cos(a) + e2 * math.sin(a)
        t = np.cross(axis, d)
        add_cube(bone, "%s_tooth_%d" % (name, k), c + d * (r * 0.96), np.column_stack([d, t, axis]), (r * 0.2, 2 * math.pi * r / teeth * 0.5,
                                                                                                       th * 0.9), region)
    for k in range(spokes):
        a = 2 * math.pi * k / spokes
        d = e1 * math.cos(a) + e2 * math.sin(a)
        beam(bone, "%s_spoke_%d" % (name, k), c + d * r * 0.18, c + d * r * 0.8, th * 0.8, region, width=r * 0.14, up=axis)
    disc(bone, name + "_hub", c, axis, r * 0.22, th * 1.5, hub, sides=8)


def handwheel(bone, name, c, axis, r=0.22, region="coral_red", spokes=4):
    """A valve handwheel: a rim of bars, spokes, a hub."""
    axis = norm(v3(*axis))
    c = v3(*c)
    ring(bone, name + "_rim", c, axis, r, 0.05, region, n=8)
    e1 = norm(np.cross(axis, v3(0, 1, 0) if abs(axis[1]) < 0.9 else v3(1, 0, 0)))
    e2 = np.cross(axis, e1)
    for k in range(spokes):
        a = math.pi * k / spokes
        d = e1 * math.cos(a) + e2 * math.sin(a)
        beam(bone, "%s_spoke%d" % (name, k), c - d * r, c + d * r, 0.03, region, up=axis)
    disc(bone, name + "_hub", c, axis, 0.05, 0.08, "in_brass", sides=6)


def pipe(bone, name, pts, d=0.22, region="in_copper", flange="in_brass", sides=6):
    """A pipe along a polyline, a flange at every joint and at both ends."""
    pts = [v3(*q) for q in pts]
    for k in range(len(pts) - 1):
        tube(bone, "lit_%s_%d" % (name, k), pts[k], pts[k + 1], d, region, sides=sides, extend=d * 0.25)
    for k, q in enumerate(pts):
        dd = pts[min(k + 1, len(pts) - 1)] - pts[max(k - 1, 0)]
        if np.linalg.norm(dd) < 1e-6:
            continue
        dn = norm(dd)
        tube(bone, "lit_%s_fl%d" % (name, k), q - dn * 0.04, q + dn * 0.04, d + 0.1, flange, sides=sides)


def valve(bone, name, p, normal, r=0.2, region="coral_red"):
    """A valve body on a pipe with its handwheel facing `normal`."""
    p = v3(*p)
    n = norm(v3(*normal))
    box(bone, "lit_%s_body" % name, p, (0.18, 0.18, 0.18), "in_brass")
    tube(bone, "lit_%s_stem" % name, p, p + n * 0.22, 0.05, "in_iron", sides=4)
    handwheel(bone, "lit_%s_wheel" % name, p + n * 0.24, n, r=r, region=region)


def gauge(bone, name, p, normal, r=0.15, red=False):
    dial(bone, "lit_%s" % name, p, normal, r, face="in_dial_red" if red else "in_gauge", rim="in_brass", depth=0.06, sides=10)


def gauge_board(bone, name, center, normal, w=1.2, h=0.8, gauges=((-0.3, 0.12, 0.16, False), (0.3, 0.12, 0.16, True), (0.0, -0.2, 0.1, False))):
    """A riveted iron board on a wall with gauges and a pipe feeding them."""
    R, u, n = frame(normal)
    c = v3(*center)
    box(bone, "lit_%s_board" % name, c + n * 0.03, (w, h, 0.06), {"all": "in_iron", "+3": "in_rivets"}, R=R, stretch=False)
    for e in (-1, 1):
        box(bone, "lit_%s_edge%d" % (name, e > 0), c + u * e * (w / 2) + n * 0.05, (0.06, h + 0.06, 0.08), "in_brass", R=R)
    for k, (dx, dy, r, red) in enumerate(gauges):
        gauge(bone, "%s_g%d" % (name, k), c + u * dx + v3(0, dy, 0) + n * 0.08, n, r=r, red=red)


def lever_bank(bone, name, p, normal, n_levers=3, tilts=(0.4, -0.3, 0.2)):
    """Iron levers with red knobs on a base plate (p on the floor, levers leaning along `normal`)."""
    R, u, n = frame(normal)
    p = v3(*p)
    w = 0.25 * n_levers + 0.1
    box(bone, "lit_%s_base" % name, p + v3(0, 0.06, 0), (w, 0.12, 0.3), "in_rivets", R=R)
    for k in range(n_levers):
        x = (k - (n_levers - 1) / 2) * 0.25
        t = tilts[k % len(tilts)]
        a = p + u * x + v3(0, 0.12, 0)
        b = a + (v3(0, 1, 0) * math.cos(t) + n * math.sin(t)) * 0.75
        beam(bone, "lit_%s_rod%d" % (name, k), a, b, 0.04, "in_iron")
        box(bone, "lit_%s_knob%d" % (name, k), b, (0.09, 0.09, 0.09), "coral_red")
        box(bone, "lit_%s_quadrant%d" % (name, k), a + v3(0, 0.08, 0), (0.03, 0.12, 0.26), "in_brass", R=R)


def pressure_tank(bone, name, p, r=0.42, h=1.6, region="in_boiler"):
    """An upright riveted pressure tank on feet, domed top, gilded bands, a gauge and a valve."""
    p = v3(*p)
    up = v3(0, 1, 0)
    prism(bone, "lit_%s_body" % name, p + up * (0.15 + h / 2), up, v3(1, 0, 0), h, r, 12, region)
    # the dome: three discs going down into the body, their caps at distinct heights (no coplanar faces)
    base = 0.15 + h
    for k in range(3):
        y0, y1 = base - 0.05 - 0.07 * k, base + 0.07 * (k + 1)
        disc(bone, "lit_%s_dome%d" % (name, k), p + up * ((y0 + y1) / 2), up, r * (0.92 - 0.25 * k), y1 - y0, region, sides=12)
    for k, y in enumerate((0.3, h * 0.55 + 0.15, h + 0.05)):
        prism(bone, "lit_%s_band%d" % (name, k), p + up * y, up, v3(1, 0, 0), 0.07, r + 0.03, 12, "in_gold")
    for k in range(3):
        a = 2 * math.pi * k / 3
        box(bone, "lit_%s_foot%d" % (name, k), p + v3(math.cos(a) * r * 0.7, 0.11, math.sin(a) * r * 0.7), (0.12, 0.22, 0.12), "in_iron")


def railing(bone, name, pts, h=1.0, step=0.7, region="in_iron"):
    """An iron railing along a polyline of base points: posts, a top rail and a middle rail."""
    pts = [v3(*q) for q in pts]
    for k in range(len(pts) - 1):
        a, b = pts[k], pts[k + 1]
        L = np.linalg.norm(b - a)
        if L < 1e-3:
            continue
        beam(bone, "lit_%s_rail%d" % (name, k), a + v3(0, h, 0), b + v3(0, h, 0), 0.07, region, extend=0.03)
        beam(bone, "lit_%s_mid%d" % (name, k), a + v3(0, h * 0.5, 0), b + v3(0, h * 0.5, 0), 0.04, region)
        nn = max(1, int(round(L / step)))
        for j in range(nn + (1 if k == len(pts) - 2 else 0)):
            q = a + (b - a) * j / nn
            beam(bone, "lit_%s_post%d_%d" % (name, k, j), q, q + v3(0, h, 0), 0.06, region)


def boiler(root, bone, Bone, c, r=1.2, h=3.3):
    """The engine room's boiler (reference panel 6): a riveted iron barrel bulging at its middle, gilded
    vertical ribs and bands, a stepped base, a domed top under a tall banded stack, a round hatch with a
    spoked emblem on its front (+z), two glowing fireboxes in the base, side drums, gauges, valves, pipes
    from the dome to the walls."""
    c = v3(*c)
    up = v3(0, 1, 0)
    e1 = v3(1, 0, 0)
    y0 = c[1]
    # base: two steps of iron and a ring of fire bricks
    prism(bone, "lit_boiler_plinth", c + up * 0.12, up, e1, 0.24, r + 0.12, 16, "in_rivets")
    prism(bone, "lit_boiler_base", c + up * 0.5, up, e1, 0.52, r - 0.02, 16, "in_brick", phase=0.1)
    prism(bone, "lit_boiler_base_band", c + up * 0.78, up, e1, 0.1, r + 0.04, 16, "in_gold")
    # the barrel: three courses (wider in the middle), riveted
    courses = ((0.83, 1.55, 0.94), (1.55, 2.35, 1.0), (2.35, 2.95, 0.92))
    for k, (a, b, s) in enumerate(courses):
        prism(bone, "lit_boiler_course%d" % k, c + up * ((a + b) / 2), up, e1, b - a, r * s, 16, "in_boiler", phase=0.05 * k)
    for k, y in enumerate((1.55, 2.35, 2.95)):
        prism(bone, "lit_boiler_band%d" % k, c + up * y, up, e1, 0.14, r * (1.0 if k == 1 else 0.96) + 0.05, 16, "in_boiler_band")
    # gilded vertical ribs
    for k in range(8):
        a = 2 * math.pi * (k + 0.5) / 8
        d = v3(math.sin(a), 0, math.cos(a))
        rib_r = r * 1.0 + 0.05
        pts = [c + up * 0.85 + d * (r * 0.95 + 0.04), c + up * 1.95 + d * rib_r, c + up * 2.95 + d * (r * 0.93 + 0.04)]
        for j in range(2):
            beam(bone, "lit_boiler_rib%d_%d" % (k, j), pts[j], pts[j + 1], 0.09, "in_gold", width=0.12, up=d)
    # domed top
    # (three discs reaching down into the barrel: their caps at distinct heights, clear of the bands', no coplanar faces)
    for k in range(3):
        t = (k + 0.5) / 3
        y0, y1 = 2.5 + 0.12 * k, 3.1 + 0.1 * k
        disc(bone, "lit_boiler_dome%d" % k, c + up * ((y0 + y1) / 2), up, min(r * 0.89, r * 0.92 * math.sqrt(1 - t * t * 0.85)), y1 - y0,
             "in_boiler", sides=16)
    # the stack up into the ceiling
    top = c + up * 3.35
    return top


def boiler_front(bone, c, r, h, root=None, Bone=None):
    """Fittings on the front (+z) of the boiler at c (its foot centre)."""
    c = v3(*c)
    up = v3(0, 1, 0)
    fz = v3(0, 0, 1)
    # round hatch with a spoked emblem, on a riveted collar reaching back into the curved barrel (no gap
    # at its sides, where the barrel turns away from it)
    hc = c + up * 1.95 + fz * (r * 1.0 + 0.04)
    zb = math.sqrt(max(0.0, r * r - 0.68 * 0.68)) - 0.03
    zf = r * 1.0 + 0.04
    disc(bone, "lit_boiler_hatch_collar", c + up * 1.95 + fz * ((zb + zf) / 2), fz, 0.68, zf - zb, "in_rivets", sides=20, phase=0.025)
    disc(bone, "lit_boiler_hatch", hc, fz, 0.62, 0.08, "in_rivets", sides=20)
    ring(bone, "lit_boiler_hatch_rim", hc + fz * 0.05, fz, 0.62, 0.09, "in_gold", n=20)
    ring(bone, "lit_boiler_hatch_rim_in", hc + fz * 0.07, fz, 0.32, 0.06, "in_gold", n=14)
    for k in range(8):
        a = 2 * math.pi * k / 8
        d = v3(math.cos(a), math.sin(a), 0)
        beam(bone, "lit_boiler_hatch_spoke%d" % k, hc + fz * 0.08 + d * 0.08, hc + fz * 0.08 + d * 0.58, 0.05, "in_gold", width=0.07, up=fz)
    disc(bone, "lit_boiler_hatch_hub", hc + fz * 0.12, fz, 0.1, 0.08, "in_brass", sides=8)
    # two fireboxes in the base
    for k, x in enumerate((-0.42, 0.42)):
        fc = c + up * 0.48 + v3(x, 0, 0) + fz * (r - 0.02)
        add_cube(bone, "glow_boiler_fire%d" % k, fc + fz * 0.04, EYE, (0.34, 0.3, 0.02), {"all": None, "+3": "in_fire", "-3": "in_fire"},
                 stretch=True)
        box(bone, "lit_boiler_firebox%d_top" % k, fc + fz * 0.07 + up * 0.18, (0.46, 0.06, 0.08), "in_iron")
        box(bone, "lit_boiler_firebox%d_sill" % k, fc + fz * 0.07 - up * 0.18, (0.46, 0.06, 0.1), "in_iron")
        for e in (-1, 1):
            box(bone, "lit_boiler_firebox%d_jamb%d" % (k, e > 0), fc + fz * 0.07 + v3(e * 0.2, 0, 0), (0.06, 0.36, 0.08), "in_iron")
    # gauges on the upper course
    for k, (x, y, rr, red) in enumerate(((-0.55, 2.7, 0.14, False), (0.0, 2.75, 0.17, True), (0.55, 2.7, 0.14, False))):
        a = math.asin(max(-0.9, min(0.9, x / r)))
        nrm = v3(math.sin(a), 0, math.cos(a))
        gauge(bone, "boiler_gauge%d" % k, c + up * y + nrm * (r * 0.93 + 0.06), nrm, r=rr, red=red)


def ladder_rungs(bone, name, a, b, w=0.5):
    """A short iron ladder against a wall from a (foot) to b (top)."""
    a, b = v3(*a), v3(*b)
    d = b - a
    side = norm(np.cross(d, v3(0, 0, 1))) if abs(d[2]) < 0.9 else v3(1, 0, 0)
    for e in (-1, 1):
        beam(bone, "lit_%s_rail%d" % (name, e > 0), a + side * e * w / 2, b + side * e * w / 2, 0.05, "in_iron")
    n = int(np.linalg.norm(d) / 0.3)
    for k in range(1, n):
        q = a + d * k / n
        beam(bone, "lit_%s_rung%d" % (name, k), q - side * w / 2, q + side * w / 2, 0.035, "in_iron")
