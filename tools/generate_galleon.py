#!/usr/bin/env python3
"""Generates the great galleon Blockbench model (.bbmodel), its textures and
its animations.

Usage:  python3 tools/generate_galleon.py

Outputs:
  blockbench/galleon.bbmodel                                     (editable in Blockbench, textures embedded)
  src/main/resources/assets/medievalships/models/entity/galleon.bbmodel  (loaded by the mod)
  src/main/resources/assets/medievalships/textures/entity/galleon.png
  src/main/resources/assets/medievalships/textures/entity/galleon_flag.png   (flags: emblem, texture #1)
  src/main/resources/assets/medievalships/textures/item/galleon.png

Same conventions and helpers as tools/generate_galley.py. The shape and the layout
come from tools/galleon_shape.py, identical to the Java collision code.

Bones used by the mod (keep their names when editing in Blockbench):
  sail_* (wind, furl)  jib  helm_wheel, rudder (steer)  flag_*, flag_*_tip, pennant_* (flag_wave)
  gunport_<l|r><n> (lid, closed/open later), cannon_<l|r><n> (the gun on its carriage, for a future combat system)
"""
import base64
import math
import os
import sys
import uuid
import zlib

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import galleon_shape as gs  # noqa: E402
import ship_details as sd  # noqa: E402
import generate_galley as gg  # noqa: E402
from galleon_texture import FLAG_SIZE, REGIONS, SIZE, make_item_icon, make_textures  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_uuid_counter = [0]


def new_uuid():
    _uuid_counter[0] += 1
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "medievalships/galleon/%d" % _uuid_counter[0]))


gg.new_uuid = new_uuid  # bones and cubes created through the galley helpers get galleon ids

v3, norm, Bone, add_cube, beam, board = gg.v3, gg.norm, gg.Bone, gg.add_cube, gg.beam, gg.board
rx, ry, rz = gg.rx, gg.ry, gg.rz
EYE = np.eye(3)
DECK_AXES = np.column_stack([np.array([0.0, 0, 1]), np.array([0.0, 1, 0]), np.array([-1.0, 0, 0])])
SIDES = ((1, "p"), (-1, "s"))
BRACE = math.radians(22)  # square yards braced round (port arms aft)


def braced(p, mast_z, a=BRACE):
    """Point of a braced yard or sail, given where it would be with the yard square."""
    o = v3(0, 0, mast_z)
    return ry(a) @ (v3(*p) - o) + o

# hull stations (dense where the shape changes fast); the visual bow closes beyond the
# collision hull end (17.5), where the half width reaches zero
STATIONS = [-17.5, -16.6, -15.6, -14.4, -13.0, -11.5, -10.0, -8.5, -7.0, -5.4, -3.7, -2.0, -0.3, 1.4,
            3.1, 4.8, 6.4, 8.0, 9.4, 10.5, 11.7, 12.8, 13.9, 14.9, 15.8, 16.6, 17.2, 17.6, 17.9]


def hw(z):
    return gs.half_width(z)


def section(z, side):
    """Outer hull cross-section (one side), from the keel to the sheer."""
    w, yk, ys = hw(z), gs.keel_y(z), gs.sheer_y(z)
    pts = [(0.08, yk)]
    for fx, fy in gs.BOTTOM_SECTION[1:]:
        pts.append((fx * w, fy * yk))
    pts += [(1.0 * w, 0.45), (0.995 * w, 1.25), (0.985 * w, ys - 0.45), (0.98 * w, ys)]
    return [v3(side * max(x, 0.08), y, z) for x, y in pts]


STRAKES = ["hull_dark", "hull_dark", "hull_mid", "hull_mid", "wood_honey", "wood_honey", "wood_honey"]


def outer_x(z, y):
    """Outer surface of the hull side (above the waterline) at height y."""
    w = hw(z)
    ys = gs.sheer_y(z)
    if y >= ys:
        return 0.98 * w
    if y >= 1.25:
        f = (y - 1.25) / max(0.01, ys - 1.25)
        return w * (0.995 - 0.015 * f)
    return w


def side_frame(z, y, side):
    """Point on the hull side and an outward frame (u along +z, v up, n outward)."""
    dz = 0.05
    p0 = v3(side * outer_x(z - dz, y), y, z - dz)
    p1 = v3(side * outer_x(z + dz, y), y, z + dz)
    u = norm(p1 - p0)
    v = v3(0, 1, 0)
    n = norm(np.cross(v, u)) * side  # outward
    if np.dot(n, v3(side, 0, 0)) < 0:
        n = -n
    return (p0 + p1) / 2, u, v, n


def decal(bone, name, z, y, side, w, h, region, depth=0.04, out=0.01, glow=False, th=None):
    """Thin flat element on the hull side (windows, gun ports, panels...)."""
    p, u, v, n = side_frame(z, y, side)
    th = th if th is not None else depth
    c = p + n * (out + th / 2)
    axes = np.column_stack([u, v, n])
    faces = {"all": region, "+1": region, "-1": region, "+2": region, "-2": region}
    return add_cube(bone, ("glow_" if glow else "") + name, c, axes, (w, h, th), faces, stretch=True,
                    u_dir=u * side * -1 if side > 0 else u, v_dir=v3(0, -1, 0))


def inner_decal(bone, name, z, y, side, w, h, region, wall=0.12, th=0.03):
    """Thin flat element on the inner face of the hull side (window seen from inside, painting...)."""
    p, u, v, n = side_frame(z, y, side)
    c = p - n * (wall + 0.02 + th / 2)
    return add_cube(bone, name, c, np.column_stack([u, v, n]), (w, h, th), {"all": None, "-3": region}, stretch=True,
                    u_dir=u * side, v_dir=v3(0, -1, 0))


def wainscot(bone, name, z0, z1, y0, y1, side, panel="panel", rail="gold", step=1.1, wall=0.12, skip=()):
    """Panelled lower wall along the inside of the hull, from z0 to z1, with a gilded rail on top;
    skip = (z_a, z_b) ranges left bare (doors, stairs)."""
    n = max(1, int(round(abs(z1 - z0) / step)))
    for k in range(n):
        za = z0 + (z1 - z0) * k / n
        zb = z0 + (z1 - z0) * (k + 1) / n
        z = (za + zb) / 2
        if any(a <= z <= b for a, b in skip):
            continue
        inner_decal(bone, "%s_%d" % (name, k), z, (y0 + y1) / 2, side, abs(zb - za) - 0.08, y1 - y0, panel, wall=wall)
        inner_decal(bone, "%s_rail_%d" % (name, k), z, y1 + 0.05, side, abs(zb - za) + 0.01, 0.08, rail, wall=wall, th=0.06)


def set_sub(cube, sub, faces=("north", "south")):
    for f in faces:
        if cube.faces.get(f):
            cube.faces[f]["sub"] = sub


# ---------------------------------------------------------------- sails
def sail_surface(origin, U, V, N, half_top, half_bottom, height, depth, fx, fy, triangle=False, round_=0.0, foot=0.0):
    """Point of a billowed sail. fx in [-1, 1] across, fy in [0, 1] from the head down.
    The belly only depends on fy: every horizontal strip is then exactly planar and shares its
    edges with its neighbours (no cracks, no overlap, no saw-tooth edges), the head stays on its
    yard / stay and the cloth curves out below it."""
    half = half_top + (half_bottom - half_top) * fy
    belly = depth * math.sin(math.pi * min(1.0, fy * (0.6 if triangle else 0.72)))
    if round_:
        # rounder sail: the belly also grows towards the middle of the width (the head stays on the yard)
        belly *= 1.0 - round_ + round_ * (1.0 - fx * fx)
    # the wind lifts the middle of the foot: the lower edge curves up between the clews
    drop = fy * height * (1.0 - foot * fy * fy * (1.0 - fx * fx))
    return origin + U * (fx * half) + V * drop + N * belly


def sail(bone, name, origin, U, V, N, half_top, half_bottom, height, depth, region, nx=1, ny=8,
         triangle=False, th=0.04, round_=0.0, overlap=0.005, foot=0.0):
    """Square (or triangle-textured) sail made of tilted strips following a curved surface.
    Each strip maps its own part of the texture region, so the cloth (and its emblem) is continuous."""
    U, V, N = norm(U), norm(V), norm(N)
    for i in range(nx):
        for j in range(ny):
            fx0, fx1 = -1 + 2 * i / nx, -1 + 2 * (i + 1) / nx
            fy0, fy1 = j / ny, (j + 1) / ny
            P = lambda a, b: sail_surface(origin, U, V, N, half_top, half_bottom, height, depth, a, b, triangle, round_, foot)  # noqa: E731
            a0, a1, b0, b1 = P(fx0, fy1), P(fx0, fy0), P(fx1, fy1), P(fx1, fy0)
            c = (a0 + a1 + b0 + b1) / 4
            u = ((b0 + b1) - (a0 + a1)) / 2
            L = np.linalg.norm(u)
            u = u / L
            vp = ((a0 - a1) + (b0 - b1)) / 2   # downwards
            H = np.linalg.norm(vp)
            v = norm(vp - np.dot(vp, u) * u)
            n = np.cross(u, v)
            if np.dot(n, N) < 0:
                u, n = -u, -n  # keep a proper rotation (flipping n alone would mirror the strip)
            axes = np.column_stack([u, v, n])
            cube = add_cube(bone, "%s_%d_%d" % (name, i, j), c, axes, (L + overlap, H + overlap, th),
                            {"all": None, "+3": region, "-3": region}, stretch=True, u_dir=U, v_dir=V)
            set_sub(cube, (i / nx, j / ny, (i + 1) / nx, (j + 1) / ny))


JIB_UC = 0.62


def jib_clew(head, tack, clew):
    """Moves the clew along the luff so that it projects at JIB_UC of it: every jib then has the same
    triangle in its texture region (they share it), at the same distance from its luff."""
    head, tack, clew = v3(*head), v3(*tack), v3(*clew)
    U = tack - head
    L = np.linalg.norm(U)
    U = U / L
    Vp = clew - head - np.dot(clew - head, U) * U
    return head + U * L * JIB_UC + Vp


def tri_sail(bone, name, head, tack, clew, depth, N, region, nx=1, ny=7):
    """Triangular sail (lateen, jib): rectangle grid spanning the triangle, transparent outside.
    head-tack = luff (U axis); returns the triangle in [0,1] region coordinates."""
    U = tack - head
    L = np.linalg.norm(U)
    U = U / L
    Vp = clew - head - np.dot(clew - head, U) * U
    H = np.linalg.norm(Vp)
    V = Vp / H
    uc = np.dot(clew - head, U) / L
    origin = head + U * (L / 2)
    sail(bone, name, origin, U, V, N, L / 2, L / 2, H, depth, region, nx=nx, ny=ny, triangle=True)
    return [(0.0, 0.0), (1.0, 0.0), (uc, 1.0)]


def lion_figurehead(bone, base, s, gold="gold", relief="carving", dark="iron", red="red_paint"):
    """Rearing crowned lion leaning out over the beakhead, facing the bow (+z); base = its chest,
    s = scale (1 = warship)."""
    B = v3(*base)

    def P(x, y, z):
        return B + v3(x, y, z) * s

    def cube(name, c, R, size, reg, **kw):
        return add_cube(bone, "figurehead_" + name, c, R, tuple(q * s for q in size), reg, **kw)
    cube("body", P(0, 0.2, -0.15), rx(-0.6), (0.85, 0.9, 1.5), gold)
    cube("chest", P(0, 0.55, 0.42), rx(-0.3), (0.8, 0.75, 0.6), gold)
    H = P(0, 1.15, 0.75)
    # mane: tufts all round the face (not under the jaw), behind the head
    for k in range(14):
        a = 2 * math.pi * k / 14
        if math.sin(a) < -0.75:
            continue
        r = 0.52 if k % 2 else 0.6
        cube("mane_%d" % k, H + v3(math.cos(a) * r, math.sin(a) * r, -0.12) * s, rz(a), (0.36, 0.26, 0.42 if k % 2 else 0.5), relief)
    cube("head", H, EYE, (0.76, 0.72, 0.7), gold)
    cube("brow", H + v3(0, 0.26, 0.34) * s, EYE, (0.62, 0.1, 0.12), relief)
    cube("muzzle", H + v3(0, -0.12, 0.44) * s, EYE, (0.48, 0.34, 0.32), gold)
    cube("nose", H + v3(0, 0.04, 0.6) * s, EYE, (0.22, 0.12, 0.08), dark)
    cube("jaw", H + v3(0, -0.4, 0.34) * s, rx(0.35), (0.42, 0.12, 0.44), gold)
    cube("tongue", H + v3(0, -0.33, 0.42) * s, rx(0.35), (0.2, 0.04, 0.3), red)
    for x in (0.2, -0.2):
        t = "l" if x > 0 else "r"
        cube("eye_" + t, H + v3(x, 0.13, 0.355) * s, EYE, (0.13, 0.08, 0.04), dark)
        cube("ear_" + t, H + v3(x * 1.55, 0.42, 0.02) * s, EYE, (0.16, 0.18, 0.1), gold)
        cube("fang_" + t, H + v3(x * 0.6, -0.31, 0.56) * s, EYE, (0.05, 0.1, 0.05), gold)
        # forelegs reaching forward, paws resting on the beak
        sh, paw = P(x * 1.5, 0.35, 0.3), P(x * 1.6, -0.35, 0.78)
        beam(bone, "figurehead_leg_" + t, sh, paw, 0.24 * s, gold)
        cube("paw_" + t, paw + v3(0, -0.05, 0.08) * s, EYE, (0.3, 0.18, 0.38), gold)
        for j in (-1, 0, 1):
            cube("claw_%s%d" % (t, j + 1), paw + v3(j * 0.09, -0.06, 0.3) * s, EYE, (0.06, 0.08, 0.08), relief)
    # crown: band and five points
    cube("crown", H + v3(0, 0.46, 0) * s, EYE, (0.6, 0.14, 0.58), gold)
    for k in range(5):
        a = math.pi * (0.1 + 0.8 * k / 4)
        cube("crown_point_%d" % k, H + v3(math.cos(a) * 0.26, 0.6, math.sin(a) * 0.24 - 0.04) * s, EYE, (0.1, 0.16, 0.1), gold)


# ---------------------------------------------------------------- galleon-only smoothing helpers
# (used by build() only: the helpers above, imported by the other generators, are left as they were)

# more hull stations where the original ones are far apart: smoother waterlines and sheer
HULL_STATIONS = []
for _a, _b in zip(STATIONS[:-1], STATIONS[1:]):
    HULL_STATIONS.append(_a)
    if _b - _a >= 1.15:
        HULL_STATIONS.append(round((_a + _b) / 2, 3))
HULL_STATIONS.append(STATIONS[-1])

TUMBLE = 0.045          # tumblehome of the castle sides (inboard lean above the sheer)
TR_CURVE = 0.22         # the transom curves forward towards its corners (plan view)
TR_COUNTER = 0.38       # the counter under the stern balcony tucks forward (rounded tuck)


def _catmull(p0, p1, p2, p3, t):
    t2, t3 = t * t, t * t * t
    return 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3)


def hull_section_2d(z):
    """(x, y) points of the outer hull cross-section (one side), keel to sheer: the bottom is a smooth
    spline through the collision section (no facet at the turn of the bilge), the topsides as before."""
    w, yk, ys = hw(z), gs.keel_y(z), gs.sheer_y(z)
    ctrl = [np.array((0.08, yk))] + [np.array((max(0.08, fx * w), fy * yk)) for fx, fy in gs.BOTTOM_SECTION[1:]]
    ctrl.append(np.array((max(0.08, w), 0.45)))
    top = [np.array((max(0.08, 0.995 * w), 1.25)), np.array((max(0.08, 0.985 * w), ys - 0.45)), np.array((max(0.08, 0.98 * w), ys))]
    ext = [np.array((2 * 0.08 - ctrl[1][0], ctrl[1][1]))] + ctrl + [top[0]]
    pts = []
    for i in range(len(ctrl) - 1):
        for t in (0.0, 0.5):
            p = _catmull(ext[i], ext[i + 1], ext[i + 2], ext[i + 3], t)
            pts.append(np.array((min(max(0.08, p[0]), max(0.08, w)), p[1])))
    pts.append(ctrl[-1])
    a = ctrl[-1]
    for b, n in ((top[0], 2), (top[1], 2), (top[2], 1)):
        for k in range(1, n + 1):
            pts.append(a + (b - a) * k / n)
        a = b
    return pts


N_UNDERWATER = 8   # strakes of hull_section_2d below the waterline point


def castle_x(z, y):
    """Outer surface of the hull side, with the tumblehome of the castles above the sheer."""
    ys = gs.sheer_y(z)
    if y <= ys:
        return outer_x(z, y)
    return 0.98 * hw(z) - TUMBLE * (y - ys) ** 1.4


def transom_z(x, y):
    """Outer face of the rounded transom: curved in plan, the counter under the balcony tucked forward."""
    f = min(1.0, abs(x) / hw(-gs.HALF_LENGTH))
    z = -gs.HALF_LENGTH + TR_CURVE * f * f
    if y < gs.MAIN_DECK_Y:
        z += TR_COUNTER * (min(1.0, (gs.MAIN_DECK_Y - y) / 1.8)) ** 1.6
    return z


def aft_z(z, x, y):
    """Station z, moved onto the curved transom for the aftmost station."""
    return transom_z(x, y) if z <= -gs.HALF_LENGTH + 1e-6 else z


def stern_half(y):
    """Half width of the transom at height y (where the hull side meets it)."""
    zt = -gs.HALF_LENGTH
    if y >= gs.sheer_y(zt):
        return castle_x(zt, y)
    pts = hull_section_2d(zt)
    for a, b in zip(pts[:-1], pts[1:]):
        if a[1] <= y <= b[1] and b[1] > a[1]:
            return a[0] + (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1])
    return pts[0][0]


def castle_frame(z, y, side):
    """Point on the (tumblehome) hull side, with u along +z, v up the surface and n outward."""
    d = 0.05
    P = lambda zz, yy: v3(side * castle_x(zz, yy), yy, zz)  # noqa: E731
    p = P(z, y)
    u = norm(P(z + d, y) - P(z - d, y))
    vv = P(z, y + d) - P(z, y - d)
    v = norm(vv - np.dot(vv, u) * u)
    n = np.cross(u, v)
    if np.dot(n, v3(side, 0, 0)) < 0:
        u, n = -u, -n
    return p, u, v, n


def frame_decal(bone, name, frame, w, h, region, out=0.01, th=0.04, glow=False, u_dir=None):
    p, u, v, n = frame
    c = p + n * (out + th / 2)
    faces = {"all": region}
    return add_cube(bone, ("glow_" if glow else "") + name, c, np.column_stack([u, v, n]), (w, h, th), faces, stretch=True,
                    u_dir=u_dir, v_dir=v3(0, -1, 0))


def _perp(d):
    d = norm(d)
    a = np.cross(d, v3(0, 1, 0))
    if np.linalg.norm(a) < 1e-3:
        a = np.cross(d, v3(1, 0, 0))
    a = norm(a)
    return a, norm(np.cross(a, d))


def round_bar(bone, name, p0, p1, d, region, extend=0.0, **kw):
    """Bar seen as round: a square beam and the same beam turned 45 degrees about its axis (8-sided outline)."""
    p0, p1 = v3(*p0), v3(*p1)
    a, b = _perp(p1 - p0)
    beam(bone, name, p0, p1, d, region, width=d, up=b, extend=extend, **kw)
    beam(bone, name + "_r", p0, p1, d * 0.94, region, width=d * 0.94, up=norm(a + b), extend=extend - 0.012, **kw)


def cap_rail(bone, name, p0, p1, th, width, region, extend=0.0, **kw):
    """Moulded cap: a wide lower band and a narrower, taller crown (rounded profile instead of a square bar)."""
    p0, p1 = v3(*p0), v3(*p1)
    dn = v3(0, th * 0.27, 0)
    beam(bone, name, p0 - dn, p1 - dn, th * 0.5, region, width=width, extend=extend, **kw)
    beam(bone, name + "_crown", p0, p1, th, region, width=width * 0.6, extend=extend - 0.012, **kw)


def wale_bar(bone, name, p0, p1, th, width, region, extend=0.0):
    """Wale with a rounded section: a tall core and a wider, thinner bead along its middle."""
    beam(bone, name, p0, p1, th, region, width=width * 0.62, extend=extend)
    beam(bone, name + "_bead", p0, p1, th * 0.58, region, width=width, extend=extend - 0.012)


def polyline(points, closed=False):
    pts = list(points)
    if closed:
        pts.append(pts[0])
    return list(zip(pts[:-1], pts[1:]))


def bezier(p0, c, p1, n):
    p0, c, p1 = v3(*p0), v3(*c), v3(*p1)
    return [(1 - t) ** 2 * p0 + 2 * (1 - t) * t * c + t * t * p1 for t in np.linspace(0, 1, n + 1)]


# ---------------------------------------------------------------- galleon-only sails (third pass)
def g_sail(bone, name, origin, U, V, N, half_top, half_bottom, height, depth, region, nx, ny, triangle=False,
           th=0.035, round_=0.0, overlap=0.02, foot=0.0, keep=None, ease=1.0):
    """Smoother sail than sail(): a fine grid of cells (the shading changes by small steps instead of a
    checkerboard), each cell fitted to its four corners on the surface by least squares so that neighbours
    meet with almost no step. keep(s0, t0, s1, t1) drops cells (fully transparent ones of a triangle).
    ease > 1 packs the rows towards the head, where the cloth bends the most."""
    U, V, N = norm(U), norm(V), norm(N)
    rows = [(j / ny) ** ease for j in range(ny + 1)]
    for i in range(nx):
        for j in range(ny):
            s0, s1 = i / nx, (i + 1) / nx
            t0, t1 = rows[j], rows[j + 1]
            if keep is not None and not keep(s0, t0, s1, t1):
                continue
            P = lambda a, b: sail_surface(origin, U, V, N, half_top, half_bottom, height, depth, 2 * a - 1, b, triangle,  # noqa: E731
                                          round_, foot)
            a0, a1, b0, b1 = P(s0, t1), P(s0, t0), P(s1, t1), P(s1, t0)
            c = (a0 + a1 + b0 + b1) / 4
            u = ((b0 + b1) - (a0 + a1)) / 2
            L = np.linalg.norm(u)
            u = u / L
            vp = ((a0 - a1) + (b0 - b1)) / 2   # downwards
            H = np.linalg.norm(vp)
            v = norm(vp - np.dot(vp, u) * u)
            # normal of the best plane through the four corners (the diagonals' cross product)
            n = norm(np.cross(b1 - a0, a1 - b0))
            if np.dot(n, N) < 0:
                n = -n
            v = norm(v - np.dot(v, n) * n)
            u = np.cross(v, n)
            if np.dot(u, (b0 + b1) - (a0 + a1)) < 0:
                u = -u
                v = np.cross(n, u)
            axes = np.column_stack([u, v, n])
            if np.linalg.det(axes) < 0:
                axes[:, 1] = -axes[:, 1]
            cube = add_cube(bone, "%s_%d_%d" % (name, i, j), c, axes, (L + overlap, H + overlap, th),
                            {"all": None, "+3": region, "-3": region}, stretch=True, u_dir=U, v_dir=V)
            set_sub(cube, (s0, t0, s1, t1))


def g_great_lantern(bone, name, foot, s, metal="gold"):
    """Great stern lantern: eight-sided lit glass between moulded rings and corner posts, a bell under it,
    a ribbed dome with a finial on top. foot = bottom of the bell. Its glass plates are named glow_* (lit, and
    left alone by lanterns.convert)."""
    foot = v3(*foot)
    up = v3(0, 1, 0)
    r, gh = 0.26 * s, 0.56 * s
    y0 = foot[1]
    turned(bone, name + "_bell", foot, foot + up * 0.26 * s, [(0, 0.1 * s), (0.25, 0.22 * s), (0.6, 0.4 * s), (1, 0)], metal)
    disc(bone, name + "_sill", foot + up * 0.3 * s, up, r + 0.05 * s, 0.08 * s, metal, n=3)
    gc = foot + up * (0.34 * s + gh / 2)
    for k in range(4):
        t = math.pi / 4 * k
        a2 = v3(math.cos(t), 0, math.sin(t))
        b2 = np.cross(a2, up)
        add_cube(bone, "glow_%s_glass_%d" % (name, k), gc, np.column_stack([a2, up, b2]),
                 (2 * r, gh * (1 - 0.02 * k), 2 * r * math.tan(math.pi / 8)),
                 {"all": "lantern", "+2": metal, "-2": metal}, stretch=True)
    rc = r / math.cos(math.pi / 8)
    for k in range(8):
        t = math.pi / 8 + math.pi / 4 * k
        p = gc + v3(math.cos(t), 0, math.sin(t)) * rc
        add_cube(bone, "%s_post_%d" % (name, k), p, np.column_stack([v3(math.cos(t), 0, math.sin(t)), up,
                 v3(-math.sin(t), 0, math.cos(t))]), (0.05 * s, gh + 0.02, 0.05 * s), metal)
    top = gc + up * (gh / 2)
    disc(bone, name + "_cornice", top + up * 0.04 * s, up, r + 0.07 * s, 0.08 * s, metal, n=3)
    turned(bone, name + "_dome", top + up * 0.08 * s, top + up * 0.44 * s,
           [(0, 0.5 * s), (0.3, 0.42 * s), (0.6, 0.28 * s), (0.85, 0.12 * s), (1, 0)], metal)
    disc(bone, name + "_knob", top + up * 0.5 * s, up, 0.07 * s, 0.1 * s, "gold")
    beam(bone, name + "_finial", top + up * 0.54 * s, top + up * 0.72 * s, 0.035 * s, "gold")
    return y0


def g_tri_sail(bone, name, head, tack, clew, depth, N, region, nx, ny, round_=0.0, ease=1.0):
    """Triangular sail with g_sail: the cells wholly outside the triangle are left out."""
    U = tack - head
    L = np.linalg.norm(U)
    U = U / L
    Vp = clew - head - np.dot(clew - head, U) * U
    H = np.linalg.norm(Vp)
    V = Vp / H
    uc = np.dot(clew - head, U) / L

    def keep(s0, t0, s1, t1):
        # the triangle is widest at the top of the cell
        return s1 > uc * t0 + 0.01 and s0 < 1 - (1 - uc) * t0 - 0.01
    g_sail(bone, name, head + U * (L / 2), U, V, N, L / 2, L / 2, H, depth, region, nx, ny, triangle=True, round_=round_,
           keep=keep, ease=ease)
    return [(0.0, 0.0), (1.0, 0.0), (uc, 1.0)]


# ---------------------------------------------------------------- galleon-only fittings (second pass)
def disc(bone, name, c, axis, r, th, region, n=2, phase=0.0):
    """Round disc (wheel, deadeye, cap, drum...) seen as a pixel circle: n=2 two crossed plates (rounded square),
    n=3 four plates turned by 45 degrees whose union is a regular octagon. Each plate is a little thinner than the
    previous one so that their faces never share a plane."""
    c, d = v3(*c), norm(v3(*axis))
    a, b = _perp(d)
    plates = [(0.0, 1.0, 0.62), (math.pi / 2, 1.0, 0.62)] if n < 3 else \
        [(math.pi / 4 * k, 1.0, math.tan(math.pi / 8)) for k in range(4)]
    for k, (t, fa, fb) in enumerate(plates):
        t += phase
        a2 = a * math.cos(t) + b * math.sin(t)
        b2 = np.cross(a2, d)
        add_cube(bone, name if k == 0 else "%s_%d" % (name, k), c, np.column_stack([a2, d, b2]),
                 (2 * r * fa, th * (1 - 0.03 * k), 2 * r * fb), region)


def turned(bone, name, p0, p1, profile, region):
    """Turned piece (post, leg, baluster, barrel, gun): profile = [(t0, d0), (t1, d1), ...] gives the diameter of
    each length of round bar between t (0 at p0, 1 at p1)."""
    p0, p1 = v3(*p0), v3(*p1)
    for k in range(len(profile) - 1):
        (ta, da), (tb, _) = profile[k], profile[k + 1]
        a, b = p0 + (p1 - p0) * ta, p0 + (p1 - p0) * tb
        disc(bone, "%s_%d" % (name, k), (a + b) / 2, b - a, da / 2, np.linalg.norm(b - a), region)


def g_barrel(bone, name, p, axis=(0, 1, 0), h=0.75, r=0.27, wood="hull_mid"):
    """Barrel with a real bulge: three round staves sections, iron hoops, end-grain heads."""
    p, d = v3(*p), norm(v3(*axis))
    q = lambda t: p + d * (h * t)  # noqa: E731
    turned(bone, name, q(0.02), q(0.98), [(0, 1.7 * r), (0.22, 1.95 * r), (0.78, 1.7 * r), (1, 0)], wood)
    for k, t in enumerate((0.12, 0.3, 0.7, 0.88)):
        disc(bone, "%s_hoop_%d" % (name, k), q(t), d, (0.89 if t in (0.12, 0.88) else 1.0) * r, 0.05, "iron")
    for k, t in enumerate((0.0, 0.985)):
        disc(bone, "%s_head_%d" % (name, k), q(t + 0.0075), d, 0.78 * r, 0.015, "end_grain")


def g_crate(bone, name, p, s=0.6, yaw=0.0, wood="dark_wood", batten="hull_light"):
    """Crate: plank box, corner battens with rounded edges, two rope lashings."""
    p = v3(*p)
    R = ry(yaw)
    add_cube(bone, name, p + v3(0, s / 2, 0), R, (s, s, s), wood)
    for i, (dx, dz) in enumerate(((1, 1), (1, -1), (-1, 1), (-1, -1))):
        c = p + R @ v3(dx * (s / 2 - 0.02), s / 2, dz * (s / 2 - 0.02))
        add_cube(bone, "%s_batten_%d" % (name, i), c, R @ ry(math.pi / 4), (0.07, s + 0.02, 0.07), batten)
    for i, t in enumerate((-0.25, 0.25)):
        add_cube(bone, "%s_lash_%d" % (name, i), p + R @ v3(t * s, s / 2, 0), R, (0.04, s + 0.03, s + 0.03), "rope")


def g_bench(bone, name, p, length, along, width=0.42, h=0.44):
    """Bench: plank seat with a rounded front edge, turned legs, a stretcher."""
    p, al = v3(*p), norm(v3(*along))
    ac = np.cross(v3(0, 1, 0), al)
    R = np.column_stack([al, v3(0, 1, 0), np.cross(al, v3(0, 1, 0))])
    add_cube(bone, name + "_seat", p + v3(0, h - 0.04, 0), R, (length, 0.08, width), {"all": "hull_light", "+2": "rail"})
    for s in (1, -1):
        round_bar(bone, name + "_edge_%d" % (s > 0), p + v3(0, h - 0.045, 0) + ac * s * width / 2 - al * length / 2,
                  p + v3(0, h - 0.045, 0) + ac * s * width / 2 + al * length / 2, 0.07, "hull_light")
    for k, t in enumerate((-0.38, 0.38)):
        b = p + al * (t * length)
        turned(bone, "%s_leg_%d" % (name, k), b, b + v3(0, h - 0.08, 0), [(0, 0.11), (0.15, 0.08), (0.5, 0.11), (0.7, 0.08), (1, 0)],
               "dark_wood")
    round_bar(bone, name + "_stretcher", p + v3(0, 0.14, 0) - al * length * 0.38, p + v3(0, 0.14, 0) + al * length * 0.38, 0.06,
              "dark_wood")


def g_hatch(bone, name, cx, cz, w, l, y):
    """Hatch: raised coaming with rounded top edges and corner posts, a slightly cambered grating inside."""
    hc = 0.2
    for k, (a, b) in enumerate(polyline([v3(-w / 2, 0, -l / 2), v3(w / 2, 0, -l / 2), v3(w / 2, 0, l / 2), v3(-w / 2, 0, l / 2)],
                                        closed=True)):
        a, b = a + v3(cx, y, cz), b + v3(cx, y, cz)
        beam(bone, "%s_coaming_%d" % (name, k), a + v3(0, hc / 2, 0), b + v3(0, hc / 2, 0), hc, "dark_wood", width=0.12)
        round_bar(bone, "%s_coaming_top_%d" % (name, k), a + v3(0, hc, 0), b + v3(0, hc, 0), 0.1, "rail", extend=-0.03)
        add_cube(bone, "%s_corner_%d" % (name, k), a + v3(0, hc / 2 + 0.01, 0), ry(math.pi / 4), (0.15, hc + 0.02, 0.15), "dark_wood")
    for s in (-1, 1):
        board(bone, "%s_grating_%d" % (name, s > 0), v3(cx, y + hc + 0.02, cz - l / 2 + 0.06), v3(cx + s * (w / 2 - 0.06), y + hc - 0.04, cz - l / 2 + 0.06),
              v3(cx, y + hc + 0.02, cz + l / 2 - 0.06), v3(cx + s * (w / 2 - 0.06), y + hc - 0.04, cz + l / 2 - 0.06), 0.05,
              "grating", v3(0, 1, 0), overlap=1.0, inner="dark_wood")


def g_capstan(bone, name, p, bars=6):
    """Capstan: round base with its pawl ring, a waisted drum with whelps, a drumhead with its bar holes."""
    p = v3(*p)
    up = v3(0, 1, 0)
    disc(bone, name + "_base", p + v3(0, 0.05, 0), up, 0.52, 0.1, "dark_wood", n=3)
    disc(bone, name + "_pawl_ring", p + v3(0, 0.13, 0), up, 0.42, 0.06, "iron", n=3)
    turned(bone, name + "_drum", p + v3(0, 0.12, 0), p + v3(0, 0.82, 0), [(0, 0.5), (0.3, 0.44), (0.7, 0.5), (1, 0)], "hull_mid")
    for k in range(8):
        a = 2 * math.pi * (k + 0.5) / 8
        o = v3(math.cos(a), 0, math.sin(a))
        beam(bone, "%s_whelp_%d" % (name, k), p + o * 0.29 + v3(0, 0.16, 0), p + o * 0.25 + v3(0, 0.78, 0), 0.08, "dark_wood",
             width=0.07, up=o)
    disc(bone, name + "_head", p + v3(0, 0.93, 0), up, 0.4, 0.22, "dark_wood", n=3)
    disc(bone, name + "_cap", p + v3(0, 1.07, 0), up, 0.22, 0.06, "gold", n=3)
    # the bars are unshipped when not heaving (the deck stays clear): only their square holes in the drumhead show
    for k in range(bars):
        a = 2 * math.pi * k / bars
        o = v3(math.cos(a), 0, math.sin(a))
        beam(bone, "%s_bar_hole_%d" % (name, k), p + o * 0.37 + v3(0, 0.93, 0), p + o * 0.43 + v3(0, 0.93, 0), 0.08, "iron")


def g_cannon(bone, name, side, z, base_y, deck_y, outer):
    """Bronze gun run out through its port, on a red truck carriage (cheeks, axletrees, four trucks, quoin),
    with its breeching rope. outer(z, y) = outer surface of the hull side."""
    y = base_y
    xo = outer(z, y)
    X = lambda d, yy=y: v3(side * (xo - d), yy, z)  # noqa: E731   (d = inboard distance from the outer planking)
    n_in, ax = v3(-side, 0, 0), v3(0, 0, 1)
    turned(bone, name + "_barrel", X(-0.14), X(1.28),
           [(0, 0.26), (0.06, 0.2), (0.45, 0.24), (0.52, 0.27), (0.75, 0.31), (0.97, 0.33), (1, 0)], "bronze")
    round_bar(bone, name + "_cascabel", X(1.28), X(1.42), 0.1, "bronze")
    disc(bone, name + "_button", X(1.44), n_in, 0.07, 0.07, "bronze")
    round_bar(bone, name + "_trunnions", X(0.78) - ax * 0.24, X(0.78) + ax * 0.24, 0.09, "bronze")
    yc = (deck_y + y) / 2
    for s in (-1, 1):
        zz = ax * s * 0.19
        beam(bone, "%s_cheek_f_%d" % (name, s > 0), X(0.42, yc + 0.04) + zz, X(0.95, yc + 0.04) + zz, y - deck_y - 0.04, "red_paint",
             width=0.08)
        beam(bone, "%s_cheek_b_%d" % (name, s > 0), X(0.95, yc - 0.06) + zz, X(1.32, yc - 0.06) + zz, y - deck_y - 0.26, "red_paint",
             width=0.08)
        for k, d in enumerate((0.55, 1.2)):
            disc(bone, "%s_truck_%d%d" % (name, s > 0, k), X(d, deck_y + 0.12) + ax * s * 0.27, ax, 0.12, 0.06, "dark_wood")
    for k, d in enumerate((0.55, 1.2)):
        round_bar(bone, "%s_axle_%d" % (name, k), X(d, deck_y + 0.12) - ax * 0.3, X(d, deck_y + 0.12) + ax * 0.3, 0.07, "dark_wood")
    beam(bone, name + "_bed", X(0.95, deck_y + 0.2), X(1.32, deck_y + 0.2), 0.06, "dark_wood", width=0.3)
    beam(bone, name + "_quoin", X(1.1, y - 0.2), X(1.32, y - 0.24), 0.07, "hull_light", width=0.2)
    for s in (-1, 1):
        beam(bone, "%s_breeching_%d" % (name, s > 0), X(1.42), X(0.15, y + 0.05) + ax * s * 0.55, 0.045, "rope")


def g_boat(bone, name, c, length=3.4, beam_=1.35, depth=0.55):
    """Ship's boat stowed on chocks: clinker strakes (white with a red sheer strake), rounded stem, small transom,
    gunwales, thwarts, a pair of oars."""
    c = v3(*c)
    ts = np.linspace(-1, 1, 9)

    def half(t):
        return 0.5 * beam_ * max(0.0, 1 - abs(t) ** (2.2 if t > 0 else 3.0)) ** 0.6 + (0.18 if t < 0 else 0.0) * (abs(t) ** 4)

    def sheer(t):
        return depth + 0.14 * t * t

    def sec(t, s):
        b = half(t)
        pts = [(0.04, 0.0), (0.55 * b, 0.06), (0.88 * b, 0.22), (b, sheer(t))]
        return [c + v3(s * max(0.04, x), yy, t * length / 2) for x, yy in pts]
    for s in (1, -1):
        for i in range(len(ts) - 1):
            A, B = sec(ts[i], s), sec(ts[i + 1], s)
            for k in range(3):
                board(bone, "%s_strake_%d%d%d" % (name, s > 0, i, k), A[k], A[k + 1], B[k], B[k + 1], 0.04, "boat", v3(s, -0.3, 0),
                      inner="hull_light")
            beam(bone, "%s_gunwale_%d%d" % (name, s > 0, i), A[3] + v3(0, 0.02, 0), B[3] + v3(0, 0.02, 0), 0.06, "rail", width=0.07,
                 extend=0.02)
    beam(bone, name + "_keel", c + v3(0, -0.03, -length / 2), c + v3(0, -0.03, length / 2), 0.07, "dark_wood", width=0.08)
    stem = bezier(c + v3(0, 0, length / 2 - 0.1), c + v3(0, 0.05, length / 2 + 0.12), c + v3(0, sheer(1) + 0.08, length / 2 + 0.1), 3)
    for j, (a, b) in enumerate(polyline(stem)):
        beam(bone, "%s_stem_%d" % (name, j), a, b, 0.08, "dark_wood", width=0.08, extend=0.03)
    zt = -length / 2
    add_cube(bone, name + "_transom", c + v3(0, sheer(-1) / 2 + 0.02, zt), EYE, (2 * half(-1) + 0.06, sheer(-1) - 0.02, 0.05), "boat")
    for k, t in enumerate((-0.55, 0.0, 0.5)):
        w = 2 * half(t) * 0.92
        add_cube(bone, "%s_thwart_%d" % (name, k), c + v3(0, depth - 0.12, t * length / 2), EYE, (w, 0.05, 0.22), "hull_light")
    add_cube(bone, name + "_floor", c + v3(0, 0.08, 0), EYE, (0.5, 0.03, length * 0.8), "deck")
    for s in (1, -1):
        round_bar(bone, "%s_oar_%d" % (name, s > 0), c + v3(s * 0.22, depth - 0.06, -length * 0.42), c + v3(s * 0.22, depth - 0.06, length * 0.36),
                  0.06, "hull_light")
        add_cube(bone, "%s_oar_blade_%d" % (name, s > 0), c + v3(s * 0.22, depth - 0.06, length * 0.36), EYE, (0.14, 0.03, 0.4), "hull_light")


def g_fife_rail(bone, name, x, z, y, half, pins=3):
    """Pin rail round a mast foot: turned posts, a moulded rail, round belaying pins with coiled falls."""
    corners = [v3(x + sx * half, 0, z + sz * half) for sx, sz in ((1, 1), (1, -1), (-1, -1), (-1, 1))]
    top = y + 0.85
    for k, cpt_ in enumerate(corners):
        turned(bone, "%s_post_%d" % (name, k), cpt_ + v3(0, y, 0), cpt_ + v3(0, top + 0.12, 0),
               [(0, 0.16), (0.1, 0.12), (0.45, 0.15), (0.6, 0.12), (0.92, 0.16), (1, 0)], "dark_wood")
    for k, (a, b) in enumerate(polyline(corners, closed=True)):
        cap_rail(bone, "%s_rail_%d" % (name, k), a + v3(0, top, 0), b + v3(0, top, 0), 0.1, 0.16, "rail", extend=0.06)
        for j in range(pins):
            q = a + (b - a) * (j + 1) / (pins + 1) + v3(0, top, 0)
            round_bar(bone, "%s_pin_%d%d" % (name, k, j), q - v3(0, 0.16, 0), q + v3(0, 0.13, 0), 0.04, "hull_light")
            if j == 1:
                o = norm(v3(q[0] - x, 0, q[2] - z))
                disc(bone, "%s_fall_%d" % (name, k), q + o * 0.06 - v3(0, 0.28, 0), o, 0.11, 0.05, "rope")


def g_pin_rail(bone, name, side, z0, z1, y, inner_x, pins=6):
    """Pin rail on the inside of the bulwark: a rounded rail on brackets, round belaying pins with coils."""
    a, b = v3(side * (inner_x(z0) - 0.1), y, z0), v3(side * (inner_x(z1) - 0.1), y, z1)
    cap_rail(bone, name, a, b, 0.09, 0.16, "rail", extend=0.04)
    for k, t in enumerate((0.1, 0.9)):
        q = a + (b - a) * t
        beam(bone, "%s_bracket_%d" % (name, k), q + v3(side * 0.06, -0.05, 0), q + v3(side * 0.06, -0.3, 0), 0.05, "dark_wood", width=0.08)
    for j in range(pins):
        q = a + (b - a) * (j + 0.5) / pins
        round_bar(bone, "%s_pin_%d" % (name, j), q - v3(0, 0.15, 0), q + v3(0, 0.12, 0), 0.04, "hull_light")
        if j % 2 == 0:
            disc(bone, "%s_coil_%d" % (name, j), q - v3(side * 0.07, 0.3, 0), v3(side, 0, 0), 0.11, 0.05, "rope")


def g_bitts(bone, name, x, z, y, h=0.85):
    """Pair of bitts: two stout posts with rounded heads and a cross piece, a turn of cable round them."""
    for s in (1, -1):
        p = v3(s * x, y, z)
        round_bar(bone, "%s_post_%d" % (name, s > 0), p, p + v3(0, h, 0), 0.24, "dark_wood")
        disc(bone, "%s_head_%d" % (name, s > 0), p + v3(0, h + 0.03, 0), v3(0, 1, 0), 0.13, 0.06, "dark_wood")
    round_bar(bone, name + "_cross", v3(-x - 0.18, y + h * 0.62, z - 0.12), v3(x + 0.18, y + h * 0.62, z - 0.12), 0.16, "hull_mid")
    round_bar(bone, name + "_cable", v3(-x, y + h * 0.35, z - 0.13), v3(x, y + h * 0.35, z - 0.13), 0.12, "rope")


def g_anchor(bone, name, top, bottom, flat):
    """Anchor hanging at the bow: ring, wooden stock with iron bands, round shank, curved arms with palms."""
    top, bottom, flat = v3(*top), v3(*bottom), norm(v3(*flat))
    d = norm(bottom - top)
    round_bar(bone, name + "_shank", top, bottom, 0.12, "iron")
    disc(bone, name + "_ring", top - d * 0.12, flat, 0.12, 0.04, "iron")
    st = np.cross(d, flat)
    round_bar(bone, name + "_stock", top + d * 0.12 - st * 0.5, top + d * 0.12 + st * 0.5, 0.11, "dark_wood")
    for s in (1, -1):
        pts = [bottom, bottom + flat * s * 0.32 - d * 0.04, bottom + flat * s * 0.5 - d * 0.32]
        for j, (a, b) in enumerate(polyline(pts)):
            round_bar(bone, "%s_arm_%d%d" % (name, s > 0, j), a, b, 0.11, "iron", extend=0.03)
        tip = pts[-1]
        e = norm(flat * s + d * 1.6)
        add_cube(bone, "%s_palm_%d" % (name, s > 0), tip + d * 0.08 - flat * s * 0.04, np.column_stack([st, e, np.cross(st, e)]),
                 (0.22, 0.2, 0.04), "iron")


# ---------------------------------------------------------------- the galleon
def build():
    root = Bone("galleon")
    hull = Bone("hull", parent=root)
    deck = Bone("deck", parent=root)
    castle_aft = Bone("sterncastle", parent=root)
    castle_fore = Bone("forecastle", parent=root)
    cabin = Bone("cabin", parent=root)
    poop = Bone("poop_house", parent=root)
    bow = Bone("bow", parent=root)
    ropes = Bone("ropes", parent=root)
    lanterns = Bone("lanterns", parent=root)
    guns = Bone("gunports", parent=root)
    main_y, fc_y, qd_y = gs.MAIN_DECK_Y, gs.FORECASTLE_Y, gs.QUARTERDECK_Y

    # ---- hull planking (tilted boards between stations: smooth, rounded hull)
    def hull_pts(z, side):
        return [v3(side * x, y, aft_z(z, x, y)) for x, y in hull_section_2d(z)]

    for side, sn in SIDES:
        for i in range(len(HULL_STATIONS) - 1):
            za, zb = HULL_STATIONS[i], HULL_STATIONS[i + 1]
            A, B = hull_pts(za, side), hull_pts(zb, side)
            for k in range(len(A) - 1):
                reg = "hull_dark" if k < 4 else ("hull_mid" if k < N_UNDERWATER else "wood_honey")
                mid = (A[k] + A[k + 1] + B[k] + B[k + 1]) / 4
                t = (A[k + 1] + B[k + 1]) - (A[k] + B[k])
                outward = norm(v3(side * t[1], -side * t[0], 0) + v3(0, 0, 0.3 * np.sign(mid[2])))
                board(hull, "hull_%s%d_%d" % (sn, i, k), A[k], A[k + 1], B[k], B[k + 1], 0.12, reg,
                      outward, inner="hull_light" if k >= N_UNDERWATER else None)
            # sheer rail (moulded cap) where there is no castle
            if gs.BULKHEAD_Z + 3.2 * 0.85 <= za and zb <= gs.FORECASTLE_START - 2.4 * 0.85:
                pa = v3(side * 0.98 * hw(za), gs.sheer_y(za) + 0.07, za)
                pb = v3(side * 0.98 * hw(zb), gs.sheer_y(zb) + 0.07, zb)
                cap_rail(hull, "rail_%s%d" % (sn, i), pa, pb, 0.16, 0.3, "rail", extend=0.05)
                # gold moulding along the hull under the rail
                pa2 = v3(side * (0.99 * hw(za) + 0.02), gs.sheer_y(za) - 0.25, za)
                pb2 = v3(side * (0.99 * hw(zb) + 0.02), gs.sheer_y(zb) - 0.25, zb)
                beam(hull, "moulding_%s%d" % (sn, i), pa2, pb2, 0.08, "wood_trim", width=0.1, extend=0.04)
            # main wale (thick dark band at the waterline), rounded
            if hw(za) > 0.6 and hw(zb) > 0.6:
                pa = v3(side * (hw(za) + 0.04), 0.85, aft_z(za, hw(za), 0.85))
                pb = v3(side * (hw(zb) + 0.04), 0.85, zb)
                wale_bar(hull, "wale_%s%d" % (sn, i), pa, pb, 0.17, 0.2, "wale", extend=0.04 if za > -17 else 0.0)
                # upper wale under the gun ports
                pa2 = v3(side * (outer_x(za, 1.25) + 0.04), 1.25, aft_z(za, hw(za), 1.25))
                pb2 = v3(side * (outer_x(zb, 1.25) + 0.04), 1.25, zb)
                beam(hull, "wale_up_%s%d" % (sn, i), pa2, pb2, 0.12, "wale", width=0.14, extend=0.04 if za > -17 else 0.0)
    # keel
    for i in range(len(HULL_STATIONS) - 1):
        za, zb = HULL_STATIONS[i], HULL_STATIONS[i + 1]
        beam(hull, "keel_%d" % i, (0, gs.keel_y(za) - 0.06, za), (0, gs.keel_y(zb) - 0.06, zb), 0.25,
             "dark_wood", width=0.35, extend=0.06)
    # sternpost: closes the rounded tuck of the counter down to the keel, in front of the rudder
    ys_ = np.linspace(gs.keel_y(-gs.HALF_LENGTH) - 0.12, main_y - 0.1, 6)
    zb_ = -gs.HALF_LENGTH - 0.06
    sp = [(v3(0, y, (transom_z(0, y) + 0.1 + zb_) / 2), transom_z(0, y) + 0.1 - zb_) for y in ys_]
    for k in range(len(sp) - 1):
        (a, da), (b, db) = sp[k], sp[k + 1]
        beam(hull, "sternpost_%d" % k, a, b, (da + db) / 2, "dark_wood", width=0.3, up=v3(0, 0, 1), extend=0.04)

    # ---- rounded transom (curved in plan, counter tucked under the balcony) with the balcony door,
    # gallery windows and carvings
    zt = -gs.HALF_LENGTH

    def tp(x, y, out=0.0):
        return v3(x, y, transom_z(x, y) - out)

    def tframe(x, y):
        """Point on the transom, axes (u ~ +x, v up, w ~ +z inboard): the outer face of a cube is its -3 face."""
        d = 0.04
        u = norm(tp(x + d, y) - tp(x - d, y))
        vv = tp(x, y + d) - tp(x, y - d)
        v = norm(vv - np.dot(vv, u) * u)
        return tp(x, y), np.column_stack([u, v, np.cross(u, v)])

    def tcube(bone, name, x, y, size, region, out=0.0, **kw):
        p, R = tframe(x, y)
        return add_cube(bone, name, p - R[:, 2] * (out + size[2] / 2), R, size, region, **kw)

    rows = [gs.keel_y(zt), -0.45, -0.1, 0.25, 0.6, main_y, 1.4, 1.8, 2.2, 2.6, gs.DOOR_TOP, 3.5, 4.05, gs.QD_RAIL_Y]
    for k in range(len(rows) - 1):
        y0, y1 = rows[k], rows[k + 1]
        ym = (y0 + y1) / 2
        reg = "hull_dark" if ym < -0.1 else ("hull_mid" if ym < main_y else "wood_honey")
        door = main_y - 1e-6 <= y0 and y1 <= gs.DOOR_TOP + 1e-6
        if door:
            cells = []
            for side in (1, -1):
                for j in range(4):
                    cells.append((lambda y, f=j / 4, s=side: s * (gs.DOOR_HALF + f * (stern_half(y) - gs.DOOR_HALF)),
                                  lambda y, f=(j + 1) / 4, s=side: s * (gs.DOOR_HALF + f * (stern_half(y) - gs.DOOR_HALF))))
        else:
            fs = np.linspace(-1, 1, 9)
            cells = [(lambda y, f=fs[j]: f * stern_half(y), lambda y, f=fs[j + 1]: f * stern_half(y)) for j in range(8)]
        for j, (xa, xb) in enumerate(cells):
            board(castle_aft, "transom_%d_%d" % (k, j), tp(xa(y0), y0), tp(xa(y1), y1), tp(xb(y0), y0), tp(xb(y1), y1), 0.2, reg,
                  v3(0, 0, -1), overlap=1.03, inner="hull_light" if ym > main_y else None)
    # quarter pieces: rounded gilded mouldings on the corners where the sides meet the transom
    for side, sn in SIDES:
        cy = [0.45, 1.2, 2.0, 2.8, 3.5, 4.1, gs.QD_RAIL_Y + 0.02]
        for j, (ya, yb) in enumerate(polyline(cy)):
            pa = tp(side * stern_half(ya), ya, 0.02)
            pb = tp(side * stern_half(yb), yb, 0.02)
            round_bar(castle_aft, "transom_quarter_%s%d" % (sn, j), pa, pb, 0.17, "gold", extend=0.03)
    # door frame (gold) and lintel carving
    tcube(castle_aft, "transom_door_lintel", 0, gs.DOOR_TOP + 0.1, (2 * gs.DOOR_HALF + 0.3, 0.2, 0.1), "gold", out=-0.03)
    tcube(castle_aft, "transom_door_arch", 0, gs.DOOR_TOP + 0.3, (2 * gs.DOOR_HALF - 0.1, 0.16, 0.08), "carving", out=-0.02,
          stretch=True)
    for side, sn in SIDES:
        tcube(castle_aft, "transom_door_jamb_" + sn, side * (gs.DOOR_HALF + 0.07), (main_y + gs.DOOR_TOP) / 2,
              (0.14, gs.DOOR_TOP - main_y, 0.1), "gold", out=-0.03)
        # gallery windows (lit) each side of the door, with arched gilded heads
        for j, x in enumerate((1.3, 1.95)):
            tcube(castle_aft, "glow_transom_window_%s%d" % (sn, j), side * x, 2.05, (0.5, 1.0, 0.06), "glow_window", out=-0.02,
                  stretch=True)
            tcube(castle_aft, "transom_window_head_%s%d" % (sn, j), side * x, 2.62, (0.6, 0.12, 0.08), "gold", out=-0.02)
            tcube(castle_aft, "transom_window_sill_%s%d" % (sn, j), side * x, 1.5, (0.6, 0.1, 0.1), "wood_trim", out=-0.03)
            p, R = tframe(side * x, 2.05)
            add_cube(cabin, "transom_window_in_%s%d" % (sn, j), p + R[:, 2] * 0.215, R, (0.5, 1.0, 0.03),
                     {"all": None, "+3": "window_in"}, stretch=True)
        for j, x in enumerate((1.0, 1.62, 2.22)):
            tcube(castle_aft, "transom_mullion_%s%d" % (sn, j), side * x, 2.05, (0.1, 1.15, 0.08), "pilaster", out=-0.02, stretch=True)
        # upper windows of the poop house level
        tcube(castle_aft, "transom_upper_window_" + sn, side * 1.25, 4.05, (0.55, 0.6, 0.06), "window", out=-0.02, stretch=True)
    arms = tp(0, 3.98)
    add_cube(castle_aft, "arms_frame", arms + v3(0, 0, -0.02), EYE, (1.55, 1.12, 0.08), "gold")
    add_cube(castle_aft, "arms_emblem", arms - v3(0, 0, 0.07), EYE, (1.35, 0.92, 0.04),
             {"all": None, "-3": "flag"}, stretch=True, u_dir=v3(1, 0, 0), v_dir=v3(0, -1, 0))
    add_cube(castle_aft, "arms_crown", arms + v3(0, 0.68, -0.06), EYE, (0.6, 0.26, 0.1), "carving", stretch=True)
    for side, sn in SIDES:
        tcube(castle_aft, "arms_supporter_" + sn, side * 0.95, 3.93, (0.22, 0.95, 0.14), "pilaster", out=-0.02, stretch=True)
    # curved cornice on top, carved friezes following the curve
    for tag, y, th, wd, out, reg, fn in (("transom_cornice", gs.QD_RAIL_Y + 0.08, 0.18, 0.4, -0.12, "gold", cap_rail),
                                         ("transom_carving", 3.25, 0.22, 0.08, 0.02, "carving", None),
                                         ("transom_carving_low", 0.6, 0.2, 0.08, 0.02, "carving", None),
                                         ("transom_moulding", 1.32, 0.09, 0.1, 0.03, "wood_trim", None)):
        hw_ = stern_half(y) + (0.1 if fn else -0.02)
        xs_ = np.linspace(-hw_, hw_, 9)
        for j, (xa, xb) in enumerate(polyline(xs_)):
            if tag == "transom_moulding" and max(abs(xa), abs(xb)) < gs.DOOR_HALF + 0.15:
                continue
            pa, pb = tp(xa, y, out), tp(xb, y, out)
            if fn:
                fn(castle_aft, "%s_%d" % (tag, j), pa, pb, th, wd, reg, extend=0.02)
            else:
                beam(castle_aft, "%s_%d" % (tag, j), pa, pb, th, reg, width=wd, extend=0.01, stretch=reg == "carving")

    # ---- stern balcony (gallery), walkable through the door
    bb, bh = gs.BALCONY_BACK, gs.BALCONY_HALF
    add_cube(castle_aft, "balcony_floor", (0, main_y - gs.BALCONY_FLOOR / 2, (bb + zt) / 2), EYE,
             (2 * bh, gs.BALCONY_FLOOR, zt - bb), {"all": "dark_wood", "+2": "deck"})
    # carved fascia under the floor edge, with gilded drops
    add_cube(castle_aft, "balcony_fascia", (0, main_y - gs.BALCONY_FLOOR - 0.08, bb + 0.05), EYE, (2 * bh - 0.1, 0.16, 0.08),
             "carving", stretch=True)
    for j, x in enumerate(np.linspace(-bh + 0.2, bh - 0.2, 6)):
        add_cube(castle_aft, "balcony_drop_%d" % j, (x, main_y - gs.BALCONY_FLOOR - 0.24, bb + 0.06), EYE, (0.1, 0.18, 0.1), "gold")
    rail_top = main_y + gs.BALCONY_RAIL
    cap_rail(castle_aft, "balcony_rail_back", (-bh + 0.02, rail_top - 0.06, bb + 0.06), (bh - 0.02, rail_top - 0.06, bb + 0.06), 0.13,
             0.16, "gold", extend=0.04)
    for side, sn in SIDES:
        cap_rail(castle_aft, "balcony_rail_" + sn, (side * (bh - 0.06), rail_top - 0.06, bb + 0.02), (side * (bh - 0.06), rail_top - 0.06, transom_z(bh, rail_top) + 0.05),
                 0.13, 0.16, "gold")
        # floor filler up to the curved transom (over the transom collision box)
        for j, (xa, xb) in enumerate(((0.0, 0.8), (0.8, 1.4), (1.4, 1.9), (1.9, bh))):
            z1 = transom_z(xb, main_y) + 0.06
            add_cube(castle_aft, "balcony_floor_fill_%s%d" % (sn, j), (side * (xa + xb) / 2, main_y - 0.06, (zt + z1) / 2), EYE,
                     (xb - xa, 0.12, z1 - zt), {"all": "dark_wood", "+2": "deck"})
        # corner posts with finials
        c = v3(side * (bh - 0.07), 0, bb + 0.07)
        round_bar(castle_aft, "balcony_post_" + sn, c + v3(0, main_y, 0), c + v3(0, rail_top + 0.02, 0), 0.15, "dark_wood")
        add_cube(castle_aft, "balcony_finial_" + sn, c + v3(0, rail_top + 0.12, 0), ry(math.pi / 4), (0.14, 0.14, 0.14), "gold")
        add_cube(castle_aft, "balcony_finial_top_" + sn, c + v3(0, rail_top + 0.24, 0), EYE, (0.07, 0.1, 0.07), "gold")
    for j, x in enumerate(np.linspace(-bh + 0.3, bh - 0.3, 8)):
        round_bar(castle_aft, "balcony_baluster_%d" % j, (x, main_y, bb + 0.06), (x, rail_top - 0.12, bb + 0.06), 0.08, "hull_light")
        add_cube(castle_aft, "balcony_baluster_bulb_%d" % j, (x, main_y + 0.3, bb + 0.06), ry(math.pi / 4), (0.12, 0.16, 0.12), "hull_light")
    for side, sn in SIDES:
        for j, z in enumerate((bb + 0.4, (bb + zt) / 2 + 0.1)):
            round_bar(castle_aft, "balcony_baluster_%s%d" % (sn, j), (side * (bh - 0.06), main_y, z),
                      (side * (bh - 0.06), rail_top - 0.12, z), 0.08, "hull_light")
        # curved brackets (knees) under the floor, from the counter
        for j, x in enumerate((bh - 0.3, 0.95)):
            x = side * x
            pts = [v3(x, -0.35, transom_z(x, -0.35) - 0.02), v3(x, 0.25, bb + 0.75), v3(x, main_y - 0.3, bb + 0.18)]
            for q, (pa, pb) in enumerate(polyline(pts)):
                beam(castle_aft, "balcony_bracket_%s%d_%d" % (sn, j, q), pa, pb, 0.14, "dark_wood", width=0.12, extend=0.05)

    # ---- castle bulwarks (above the sheer), leaning inboard (tumblehome), with moulded caps
    def cpt(z, y, side, dx=0.0):
        x = castle_x(z, y) + dx
        return v3(side * x, y, aft_z(z, x, y))

    def bulwark(bone, tag, z0, z1, top_y):
        zs = [z0] + [z for z in HULL_STATIONS if z0 < z < z1] + [z1]
        for side, sn in SIDES:
            for i in range(len(zs) - 1):
                za, zb = zs[i], zs[i + 1]
                for r in range(2):
                    def yy(z, rr):
                        y0 = gs.sheer_y(z) - 0.05
                        return y0 + (top_y - y0) * rr / 2
                    board(bone, "%s_wall_%s%d_%d" % (tag, sn, i, r), cpt(za, yy(za, r), side), cpt(za, yy(za, r + 1), side),
                          cpt(zb, yy(zb, r), side), cpt(zb, yy(zb, r + 1), side), 0.12, "wood_honey", v3(side, 0, 0),
                          inner="hull_light")
                cap_rail(bone, "%s_cap_%s%d" % (tag, sn, i), cpt(za, top_y, side, -0.04) + v3(0, 0.08, 0),
                         cpt(zb, top_y, side, -0.04) + v3(0, 0.08, 0), 0.17, 0.32, "wood_trim", extend=0.05)
                wale_bar(bone, "%s_band_%s%d" % (tag, sn, i), cpt(za, top_y - 0.35, side, 0.03), cpt(zb, top_y - 0.35, side, 0.03),
                         0.09, 0.08, "wood_trim", extend=0.03)

    def sweep(bone, tag, zc, dirn, top_y, length=1.5, n=6):
        """Where the raised castle side meets the waist: the bulwark top, its cap and the moulding band run down
        to the waist rail in one long ogee (S) curve instead of a square step."""
        zs = [zc + dirn * length * k / n for k in range(n + 1)]

        def top(z):
            t = min(1.0, abs(z - zc) / length)
            ys = gs.sheer_y(z)
            return ys + 0.07 + (top_y - ys - 0.07) * ogee(t)

        def ogee(t):
            t = min(1.0, max(0.0, t))
            return 1.0 - t * t * t * (t * (6 * t - 15) + 10)   # smootherstep: flat at both ends

        def band(z):
            t = min(1.0, abs(z - zc) / length)
            return (gs.sheer_y(z) - 0.25) + (top_y - 0.35 - gs.sheer_y(z) + 0.25) * ogee(t)
        for side, sn in SIDES:
            for i in range(n):
                za, zb = zs[i], zs[i + 1]
                ya, yb = top(za), top(zb)
                if i < n - 1:
                    board(bone, "%s_sweep_%s%d" % (tag, sn, i), cpt(za, gs.sheer_y(za) - 0.05, side), cpt(za, ya, side),
                          cpt(zb, gs.sheer_y(zb) - 0.05, side), cpt(zb, yb, side), 0.12, "wood_honey", v3(side, 0, 0),
                          inner="hull_light")
                cap_rail(bone, "%s_sweep_cap_%s%d" % (tag, sn, i), cpt(za, ya, side, -0.04) + v3(0, 0.08, 0),
                         cpt(zb, yb, side, -0.04) + v3(0, 0.08, 0), 0.17, 0.32 - 0.02 * i / n, "wood_trim", extend=0.05)
                # the moulding band of the castle curves down into the waist moulding
                wale_bar(bone, "%s_sweep_band_%s%d" % (tag, sn, i), cpt(za, band(za), side, 0.03), cpt(zb, band(zb), side, 0.03),
                         0.09, 0.08, "wood_trim", extend=0.03)
            # carved scrolls (drifts) at both ends of the curve
            add_cube(bone, "%s_scroll_%s" % (tag, sn), cpt(zc, top_y - 0.12, side, 0.04) + v3(0, 0, dirn * 0.1), rx(math.pi / 4),
                     (0.14, 0.2, 0.2), "gold")
            ze = zc + dirn * length * 0.82
            ye = top(ze)
            add_cube(bone, "%s_scroll_end_%s" % (tag, sn), cpt(ze, ye - 0.14, side, 0.05), rx(math.pi / 4), (0.12, 0.15, 0.15), "gold")
            add_cube(bone, "%s_scroll_end_b_%s" % (tag, sn), cpt(ze, ye - 0.14, side, 0.09), EYE, (0.06, 0.08, 0.08), "carving")

    bulwark(castle_aft, "qd", -gs.HALF_LENGTH, gs.BULKHEAD_Z, gs.QD_RAIL_Y)
    bulwark(castle_fore, "fc", gs.FORECASTLE_START, 17.9, gs.FC_RAIL_Y)
    sweep(castle_aft, "qd", gs.BULKHEAD_Z, 1, gs.QD_RAIL_Y, length=3.2, n=10)
    sweep(castle_fore, "fc", gs.FORECASTLE_START, -1, gs.FC_RAIL_Y, length=2.4, n=8)
    # stern castle side decoration: painted panels and lit cabin windows
    for side, sn in SIDES:
        u_hint = v3(0, 0, -side)
        for j, z in enumerate((-16.0, -14.4, -12.8, -11.2, -9.6)):
            if j > 1:
                frame_decal(castle_aft, "qd_window_%s%d" % (sn, j), castle_frame(z, gs.QD_RAIL_Y - 0.5, side), 0.55, 0.5,
                            "glow_window", glow=True, u_dir=u_hint)
            if j > 0:
                frame_decal(castle_aft, "qd_post_%s%d" % (sn, j), castle_frame(z + 0.8, gs.QD_RAIL_Y - 0.5, side), 0.12, 0.9,
                            "dark_wood", out=0.02, u_dir=u_hint)
        for j, z in enumerate((-15.4, -13.0, -10.6)):
            if j > 0:
                decal(cabin, "cabin_window_%s%d" % (sn, j), z, 2.2, side, 0.6, 0.75, "glow_window", glow=True)
            inner_decal(cabin, "cabin_window_in_%s%d" % (sn, j), z, 2.2, side, 0.6, 0.75, "window_in")
        for j, z in enumerate((11.6, 13.4, 15.2)):
            frame_decal(castle_fore, "fc_window_%s%d" % (sn, j), castle_frame(z, gs.FC_RAIL_Y - 0.5, side), 0.5, 0.45,
                        "glow_window", glow=True, u_dir=u_hint)

        # quarter gallery: a bow-fronted closed balcony on each stern corner, domed roof, carved corbel and pendant
        qz0, qz1, D, ng = -16.95, -14.25, 0.62, 6
        ts = np.linspace(0, 1, ng + 1)

        def gp(t, y, d):
            z = qz0 + (qz1 - qz0) * t
            return v3(side * (castle_x(z, y) + d * math.sin(math.pi * t) ** 0.75), y, z)

        def ring(bone, tag, y0, d0, y1, d1, reg, th=0.1):
            for i in range(ng):
                a0, a1, b0, b1 = gp(ts[i], y0, d0), gp(ts[i], y1, d1), gp(ts[i + 1], y0, d0), gp(ts[i + 1], y1, d1)
                mid = (a0 + a1 + b0 + b1) / 4
                outward = mid - gp(0.5, (y0 + y1) / 2, 0) + v3(0, (y1 - y0) * 0.0, 0)
                if d1 < d0 and y1 > y0:
                    outward = outward + v3(0, 0.6, 0)
                if d1 < d0 and y1 < y0:
                    outward = outward - v3(0, 0.6, 0)
                board(bone, "%s_%s%d" % (tag, sn, i), a0, a1, b0, b1, th, reg, outward, overlap=1.03)

        for r, (y0, y1, reg) in enumerate(((1.75, 2.0, "wood_trim"), (2.0, 3.2, "wood_honey"), (3.2, 3.45, "red_paint"))):
            ring(castle_aft, "quarter_gallery_%d" % r, y0, D, y1, D, reg)
        for r, (y0, d0, y1, d1) in enumerate(((3.47, D + 0.04, 3.72, 0.52), (3.72, 0.52, 3.92, 0.36), (3.92, 0.36, 4.06, 0.18),
                                              (4.06, 0.18, 4.12, 0.0))):
            ring(castle_aft, "quarter_gallery_dome_%d" % r, y0, d0, y1, d1, "roof", th=0.08)
        for r, (y0, d0, y1, d1, reg) in enumerate(((1.74, D, 1.46, 0.72 * D, "carving"), (1.46, 0.72 * D, 1.2, 0.42 * D, "wood_trim"),
                                                   (1.2, 0.42 * D, 1.0, 0.12 * D, "wood_trim"))):
            ring(castle_aft, "quarter_gallery_corbel_%d" % r, y0, d0, y1, d1, reg, th=0.08)
        for i in range(ng):
            cap_rail(castle_aft, "quarter_gallery_cornice_%s%d" % (sn, i), gp(ts[i], 3.48, D + 0.03), gp(ts[i + 1], 3.48, D + 0.03),
                     0.12, 0.16, "gold", extend=0.03)
            beam(castle_aft, "quarter_gallery_sill_%s%d" % (sn, i), gp(ts[i], 1.76, D + 0.03), gp(ts[i + 1], 1.76, D + 0.03),
                 0.1, "wood_trim", width=0.12, extend=0.03)
            if 1 <= i <= ng - 2:
                a, b = gp(ts[i], 2.62, D), gp(ts[i + 1], 2.62, D)
                u = norm(b - a)
                n_ = norm(np.cross(u, v3(0, 1, 0)))
                if np.dot(n_, v3(side, 0, 0)) < 0:
                    u, n_ = -u, -n_
                frame_decal(castle_aft, "quarter_window_%s%d" % (sn, i), ((a + b) / 2, u, v3(0, 1, 0), n_),
                            np.linalg.norm(b - a) * 0.72, 0.95, "arch_window", out=0.005, th=0.04, glow=True)
        for i in range(1, ng):
            a, b = gp(ts[i] - 0.02, 2.6, D), gp(ts[i] + 0.02, 2.6, D)
            u = norm(b - a)
            n_ = norm(np.cross(u, v3(0, 1, 0)))
            if np.dot(n_, v3(side, 0, 0)) < 0:
                u, n_ = -u, -n_
            c = (a + b) / 2 + n_ * 0.02
            add_cube(castle_aft, "quarter_gallery_pilaster_%s%d" % (sn, i), c, np.column_stack([u, v3(0, 1, 0), n_]),
                     (0.08, 1.2, 0.05), "pilaster", stretch=True)
        top_c = gp(0.5, 4.1, 0.1)
        add_cube(castle_aft, "quarter_gallery_finial_" + sn, top_c + v3(0, 0.08, 0), ry(math.pi / 4), (0.14, 0.14, 0.14), "gold")
        add_cube(castle_aft, "quarter_gallery_finial_top_" + sn, top_c + v3(0, 0.2, 0), EYE, (0.06, 0.12, 0.06), "gold")
        low_c = gp(0.5, 1.0, 0.1)
        round_bar(castle_aft, "quarter_gallery_pendant_" + sn, low_c + v3(0, 0.02, 0), low_c - v3(0, 0.3, 0), 0.1, "gold")
        add_cube(castle_aft, "quarter_gallery_pendant_ball_" + sn, low_c - v3(0, 0.34, 0), ry(math.pi / 4), (0.13, 0.13, 0.13), "gold")
        # chain-wales (channels) carrying the deadeyes of the shrouds, with their chains
        for tag, z0, z1 in (("main", -1.0, 2.8), ("fore", 11.0, 13.4), ("mizzen", -13.6, -11.6)):
            zm = (z0 + z1) / 2
            y = gs.rail_y(zm) - 0.22
            beam(hull, "channel_%s_%s" % (tag, sn), (side * (castle_x(z0, y) + 0.16), y, z0), (side * (castle_x(z1, y) + 0.16), y, z1),
                 0.1, "dark_wood", width=0.36)
            # rounded outer edge (moulding) and two supporting knees under the channel
            round_bar(hull, "channel_edge_%s_%s" % (tag, sn), (side * (castle_x(z0, y) + 0.33), y + 0.01, z0),
                      (side * (castle_x(z1, y) + 0.33), y + 0.01, z1), 0.12, "wood_trim", extend=0.02)
            for j, zk in enumerate((z0 + 0.35, z1 - 0.35)):
                beam(hull, "channel_knee_%s_%s%d" % (tag, sn, j), (side * (castle_x(zk, y - 0.45) + 0.03), y - 0.45, zk),
                     (side * (castle_x(zk, y) + 0.28), y - 0.04, zk), 0.08, "dark_wood", width=0.1)

    # ---- decks
    def deck_span(bone, z0, z1, n, y, tag, under="dark_wood"):
        for j in range(n):
            za = z0 + (z1 - z0) * j / n
            zb = z0 + (z1 - z0) * (j + 1) / n
            w = max(gs.inner_half_width(za), gs.inner_half_width(zb)) + 0.1
            # turned a quarter round: the planks of the texture run fore and aft
            # (two halves, so that the planks keep their real width)
            for h_, s_ in ((0, 1), (1, -1)):
                add_cube(bone, "deck_%s%d%s" % (tag, j, "_b" if h_ else ""), (s_ * w / 2, y - 0.075, (za + zb) / 2), DECK_AXES,
                         (zb - za + 0.02, 0.15, w), {"all": "deck", "-2": under})

    deck_span(deck, -17.28, gs.FORECASTLE_START, 14, main_y, "main")
    deck_span(castle_fore, gs.FORECASTLE_START, gs.DECK_MAX_Z, 4, fc_y, "fore")
    deck_span(castle_aft, -17.26, gs.BULKHEAD_Z, 6, qd_y, "quarter")
    # forecastle front wall (with a carved door) and quarterdeck bulkhead (real door to the cabin)
    wf = gs.inner_half_width(gs.FORECASTLE_START) + 0.12
    add_cube(castle_fore, "fc_front", (0, (main_y + fc_y) / 2, gs.FORECASTLE_START), EYE, (2 * wf, fc_y - main_y, 0.16),
             {"all": "wood_honey", "+3": "hull_light"})
    add_cube(castle_fore, "fc_front_door", (0, main_y + 0.8, gs.FORECASTLE_START - 0.09), EYE, (0.8, 1.55, 0.04), "door", stretch=True)
    for side, sn in SIDES:
        add_cube(castle_fore, "fc_front_window_" + sn, (side * 1.1, main_y + 1.3, gs.FORECASTLE_START - 0.09), EYE,
                 (0.45, 0.45, 0.04), "window", stretch=True)
    bz0, bz1 = gs.BULKHEAD_Z - gs.BULKHEAD_THICK, gs.BULKHEAD_Z
    bw = gs.inner_half_width(bz0) + 0.12
    slab_bottom = qd_y - gs.QUARTERDECK_SLAB
    for side, sn in SIDES:
        x0, x1 = gs.DOOR_HALF, bw
        add_cube(cabin, "bulkhead_" + sn, (side * (x0 + x1) / 2, (main_y + slab_bottom) / 2, (bz0 + bz1) / 2), EYE,
                 (x1 - x0, slab_bottom - main_y, bz1 - bz0), {"all": "wood_honey", "-3": "hull_light"})
        add_cube(cabin, "bulkhead_jamb_" + sn, (side * (gs.DOOR_HALF + 0.07), (main_y + gs.DOOR_TOP) / 2, bz1 + 0.02), EYE,
                 (0.14, gs.DOOR_TOP - main_y, 0.08), "gold")
        add_cube(cabin, "bulkhead_window_" + sn, (side * 2.0, 2.15, bz1 + 0.02), EYE, (0.6, 0.7, 0.05), "window", stretch=True)
        add_cube(cabin, "bulkhead_window_in_" + sn, (side * 2.0, 2.15, bz0 - 0.02), EYE, (0.6, 0.7, 0.03),
                 {"all": None, "-3": "window_in"}, stretch=True)
        add_cube(cabin, "bulkhead_pillar_" + sn, (side * 3.0, (main_y + slab_bottom) / 2, bz1 + 0.06), EYE,
                 (0.18, slab_bottom - main_y, 0.12), "gold")
    add_cube(cabin, "bulkhead_lintel", (0, (gs.DOOR_TOP + slab_bottom) / 2, (bz0 + bz1) / 2), EYE,
             (2 * gs.DOOR_HALF, slab_bottom - gs.DOOR_TOP, bz1 - bz0), "wood_honey")
    add_cube(cabin, "bulkhead_door_arch", (0, gs.DOOR_TOP + 0.06, bz1 + 0.03), EYE, (2 * gs.DOOR_HALF + 0.3, 0.12, 0.1), "gold")
    # slab edge (front of the quarterdeck)
    for j in range(4):
        x0_ = -bw + 2 * bw * j / 4
        add_cube(castle_aft, "quarterdeck_edge_%d" % j, (x0_ + bw / 4, qd_y - 0.15, bz1 + 0.02), EYE, (bw / 2, 0.3, 0.06),
                 {"all": "carving", "+2": "wood_trim", "-2": "wood_trim"}, stretch=True)

    # ---- great cabin interior: chairs (seats), lanterns, chest, table against the side
    for side, sn in SIDES:
        # armchairs (seats): turned legs, velvet cushion, carved back with a gilt crest rail
        x, z = side * 2.2, -13.0
        add_cube(cabin, "chair_seat_" + sn, (x, main_y + 0.42, z), EYE, (0.55, 0.08, 0.55), "hull_light")
        add_cube(cabin, "chair_cushion_" + sn, (x, main_y + 0.49, z), EYE, (0.48, 0.07, 0.48), "velvet")
        add_cube(cabin, "chair_back_" + sn, (x + side * 0.24, main_y + 0.82, z), EYE, (0.07, 0.66, 0.46), {"all": "wood_honey", "-1" if side > 0 else "+1": "velvet"})
        round_bar(cabin, "chair_crest_" + sn, (x + side * 0.24, main_y + 1.17, z - 0.3), (x + side * 0.24, main_y + 1.17, z + 0.3), 0.08, "gold")
        for dx in (-0.22, 0.22):
            for dz in (-0.22, 0.22):
                top_y = main_y + (1.12 if dx * side > 0 else 0.4)
                turned(cabin, "chair_leg_%s%d%d" % (sn, int(dx > 0), int(dz > 0)), (x + dx, main_y, z + dz), (x + dx, top_y, z + dz),
                       [(0, 0.07), (0.15, 0.09), (0.35, 0.06), (1, 0)] if top_y < main_y + 0.5 else [(0, 0.07), (0.1, 0.09), (0.2, 0.06), (1, 0)],
                       "dark_wood")
        for j, zw in enumerate((-15.4, -13.0, -10.6)):
            # velvet curtains drawn either side of the cabin windows, a gilt pelmet over them
            for s_ in (-1, 1):
                inner_decal(cabin, "cabin_curtain_%s%d%d" % (sn, j, s_ > 0), zw + s_ * 0.42, 2.12, side, 0.22, 1.0, "curtain", wall=0.15,
                            th=0.05)
            inner_decal(cabin, "cabin_pelmet_%s%d" % (sn, j), zw, 2.68, side, 1.12, 0.14, "carving", wall=0.15, th=0.07)
        # cushioned locker seat under the stern windows
        x0, x1 = 0.95, 2.05
        zs = transom_z(x1, main_y + 0.5) + 0.2
        add_cube(cabin, "stern_seat_" + sn, (side * (x0 + x1) / 2, main_y + 0.22, zs + 0.22), EYE, (x1 - x0, 0.44, 0.42),
                 {"all": "wood_honey", "+3": "panel"}, stretch=True)
        add_cube(cabin, "stern_seat_cushion_" + sn, (side * (x0 + x1) / 2, main_y + 0.49, zs + 0.21), EYE, (x1 - x0 - 0.04, 0.1, 0.4), "velvet")
        round_bar(cabin, "stern_seat_edge_" + sn, (side * x0, main_y + 0.43, zs + 0.43), (side * x1, main_y + 0.43, zs + 0.43), 0.06, "gold")
        add_cube(lanterns, "cabin_lantern_" + sn, (side * 1.6, 2.5, bz0 - 0.18), EYE, (0.3, 0.42, 0.3),
                 {"all": "lantern", "+2": "iron", "-2": "iron"}, stretch=True)
        add_cube(lanterns, "glow_cabin_lantern_" + sn, (side * 1.6, 2.5, bz0 - 0.18), EYE, (0.2, 0.3, 0.2), "glow", stretch=True)
    add_cube(cabin, "cabin_chest", (2.6, main_y + 0.3, -16.3), EYE, (0.9, 0.6, 0.55), {"all": "dark_wood", "+2": "iron"})
    # deck beams under the quarterdeck: moulded (rounded lower edge), with hanging knees against the sides
    for j, zb in enumerate((-9.6, -10.85, -12.0, -13.6, -15.0, -16.3)):
        hwb = gs.inner_half_width(zb) - 0.02
        beam(cabin, "cabin_ceiling_beam_%d" % j, (-hwb, slab_bottom - 0.08, zb), (hwb, slab_bottom - 0.08, zb), 0.16, "dark_wood", width=0.24)
        round_bar(cabin, "cabin_ceiling_bead_%d" % j, (-hwb, slab_bottom - 0.17, zb), (hwb, slab_bottom - 0.17, zb), 0.1, "dark_wood",
                  extend=-0.05)
        for side in (1, -1):
            beam(cabin, "cabin_knee_%d%d" % (j, side > 0), (side * (hwb - 0.42), slab_bottom - 0.14, zb), (side * (hwb - 0.04), slab_bottom - 0.62, zb),
                 0.1, "dark_wood", width=0.14)
    # furnishing: carpet, chart table and dining table by the two chairs, bunk, bookshelf,
    # weapon rack, globe, paintings between the windows, lanterns hanging from the beams
    sd.rug(gg, cabin, "cabin_rug", (0, main_y, -13.8), 1.9, 4.6)
    sd.chandelier(gg, cabin, "cabin_chandelier", (0, slab_bottom - 0.12, -15.4), drop=0.4, r=0.38)
    for side, sn in SIDES:
        wainscot(cabin, "cabin_wainscot_" + sn, -9.9, -16.9, main_y + 0.12, main_y + 0.62, side)
    for side, sn in SIDES:
        sd.table(gg, cabin, "cabin_table_" + sn, (side * 1.35, main_y, -13.0), 0.7, 0.95, h=0.75)
        sd.hanging_lantern(gg, lanterns, "cabin_hanging_lantern_" + sn, (side * 1.3, slab_bottom - 0.2, -15.0), drop=0.2)
        p, u, v, n = side_frame(-11.8, 2.3, side)
        sd.painting(gg, cabin, "cabin_painting_" + sn, p - n * 0.14, -n, w=0.75, h=0.55)
    top = main_y + 0.75
    sd.chart_on_table(gg, cabin, "cabin_chart", (1.35, top, -13.1), yaw=math.pi / 2)
    sd.candle(gg, cabin, "cabin_candle_p", (1.45, top, -12.68))
    sd.tableware(gg, cabin, "cabin_dinner", (-1.35, top, -13.0), yaw=math.pi / 2)
    sd.candle(gg, cabin, "cabin_candle_s", (-1.4, top, -13.4))
    sd.bunk(gg, cabin, "cabin_bunk", (-2.0, main_y, -15.3), l=1.8, w=0.85)
    sd.globe(gg, cabin, "cabin_globe", (2.6, main_y + 0.6, -16.3))
    sd.bookshelf(gg, cabin, "cabin_books", (3.1, main_y, bz0 - 0.19), yaw=math.pi, w=1.0, h=1.9)
    sd.weapon_rack(gg, cabin, "cabin_arms", (-3.1, main_y, bz0), (0, 0, -1), w=1.0)

    # ---- stairs (match the collision boxes) and guard rails
    d = gs.STEP_DEPTH
    for k in range(1, 6):
        top = main_y + (qd_y - main_y) * k / 5.0
        z_front = gs.QD_STAIR_START - (k - 1) * d
        for side, sn in SIDES:
            add_cube(deck, "qd_step_%s%d" % (sn, k), (side * (gs.STAIR_X0 + gs.STAIR_X1) / 2, (main_y + top) / 2, z_front - d / 2),
                     EYE, (gs.STAIR_X1 - gs.STAIR_X0, top - main_y, d), {"all": "dark_wood", "+2": "deck"})
    for k in range(1, 5):
        top = main_y + (fc_y - main_y) * k / 4.0
        z_back = gs.FC_STAIR_START + (k - 1) * d
        for side, sn in SIDES:
            add_cube(deck, "fc_step_%s%d" % (sn, k), (side * (gs.FC_STAIR_X0 + gs.FC_STAIR_X1) / 2, (main_y + top) / 2, z_back + d / 2),
                     EYE, (gs.FC_STAIR_X1 - gs.FC_STAIR_X0, top - main_y, d), {"all": "dark_wood", "+2": "deck"})
    for side, sn in SIDES:
        # stair hand rails (inner side)
        round_bar(deck, "qd_handrail_" + sn, (side * gs.STAIR_X0, main_y + 0.9, gs.QD_STAIR_START), (side * gs.STAIR_X0, qd_y + 0.9, gs.BULKHEAD_Z),
             0.08, "rail")
        round_bar(deck, "fc_handrail_" + sn, (side * gs.FC_STAIR_X0, main_y + 0.9, gs.FC_STAIR_START),
             (side * gs.FC_STAIR_X0, fc_y + 0.9, gs.FORECASTLE_START), 0.08, "rail")

    def guard_rail(bone, tag, half, y, z):
        cap_rail(bone, tag + "_top", (-half, y + gs.RAIL_HEIGHT - 0.05, z), (half, y + gs.RAIL_HEIGHT - 0.05, z), 0.1, gs.RAIL_THICK + 0.04,
                 "gold", extend=0.05)
        for j, x in enumerate(np.linspace(-half, half, 7)):
            round_bar(bone, "%s_baluster_%d" % (tag, j), (x, y, z), (x, y + gs.RAIL_HEIGHT - 0.1, z), 0.1, "hull_light")

    guard_rail(castle_aft, "qd_rail", gs.STAIR_X0 - 0.1, qd_y, gs.BULKHEAD_Z - gs.RAIL_THICK / 2)
    guard_rail(castle_fore, "fc_rail", gs.FC_STAIR_X0 - 0.1, fc_y, gs.FORECASTLE_START + gs.RAIL_THICK / 2)

    # ---- main deck life: benches (seats), hatches, capstan-less coils, barrels
    for k, z in enumerate(gs.BENCH_Z):
        for side, sn in SIDES:
            g_bench(deck, "bench_%s%d" % (sn, k), (side * 3.1, main_y, z), 1.0, (0, 0, 1), width=0.5)
    # benches under the other seats: quarterdeck (inboard of the mizzen shrouds) and forecastle
    for side, sn in SIDES:
        g_bench(castle_aft, "qd_bench_" + sn, (side * 2.75, qd_y, -11.4), 1.0, (0, 0, 1))
        g_bench(castle_fore, "fc_bench_" + sn, (side * 2.25, fc_y, 11.6), 1.0, (0, 0, 1))
    g_bench(castle_fore, "fc_bench_bow", (0, fc_y, 15.45), 1.1, (1, 0, 0))
    g_hatch(deck, "hatch_main", 0, -1.5, 1.6, 1.6, main_y)
    g_hatch(deck, "hatch_fore", 0, 6.0, 1.3, 1.3, main_y)
    g_hatch(deck, "hatch_aft", 0, -5.0, 1.3, 1.3, main_y)
    g_capstan(deck, "capstan", (0, main_y, -3.3))
    # the ship's boat stowed on chocks over the fore hatch
    for k, z in enumerate((5.0, 7.0)):
        add_cube(deck, "boat_chock_%d" % k, (0, main_y + 0.15, z), EYE, (1.0, 0.3, 0.16), "dark_wood")
    g_boat(deck, "boat", (0, main_y + 0.3, 6.0))
    # deck details: pin rails at the mast feet and along the bulwarks, bitts, barrels, crates, coils, bucket, the bell
    g_fife_rail(deck, "fife_main", 0.0, gs.MAIN_MAST_Z, main_y, 0.95)
    g_fife_rail(castle_fore, "fife_fore", 0.0, gs.FORE_MAST_Z, fc_y, 0.75, pins=2)
    for side, sn in SIDES:
        g_pin_rail(deck, "pin_rail_main_" + sn, side, -0.9, 2.5, gs.sheer_y(0.8) - 0.22, gs.inner_half_width)
        g_pin_rail(castle_fore, "pin_rail_fore_" + sn, side, 11.2, 13.2, gs.FC_RAIL_Y - 0.25, gs.inner_half_width, pins=4)
    g_bitts(deck, "bitts", 1.0, gs.FORECASTLE_START - 0.35, main_y)
    g_barrel(deck, "barrel_w0", (3.25, main_y, 1.25))
    g_barrel(deck, "barrel_w1", (3.55, main_y, 1.75), h=0.6, r=0.22)
    g_barrel(deck, "barrel_w2", (2.95, main_y + 0.27, 1.75), axis=(-0.2, 0, 1), h=0.7, r=0.25)
    g_crate(deck, "crate_w0", (-3.25, main_y, 1.35), s=0.6, yaw=0.15)
    g_crate(deck, "crate_w1", (-3.2, main_y + 0.6, 1.3), s=0.45, yaw=-0.2)
    sd.rope_coil(gg, deck, "coil_main", (1.5, main_y, 3.1))
    sd.rope_coil(gg, deck, "coil_main2", (-1.5, main_y, 0.1))
    sd.rope_coil(gg, castle_fore, "coil_fore", (1.2, fc_y, 14.6), r=0.28)
    sd.bucket(gg, deck, "bucket", (1.2, main_y, -0.2))
    sd.bell(gg, castle_fore, "bell", (0.0, fc_y, 11.0))
    for j, x in enumerate((-0.95, 0.95)):
        g_barrel(deck, "barrel_%d" % j, (x, main_y, 9.35), h=0.7, r=0.25)

    # ---- gun ports: frame, lid (bone: can open later), empty cannon bones for a future combat system
    for side, sn in SIDES:
        tag = "l" if side > 0 else "r"
        for k, z in enumerate(gs.GUNPORT_Z):
            decal(guns, "gunport_frame_%s%d" % (tag, k + 1), z, gs.GUNPORT_Y, side, 0.62, 0.58, "gunport", out=0.0)
            p, u, v, n = side_frame(z, gs.GUNPORT_Y + 0.3, side)
            hinge = p + n * 0.05
            lid = Bone("gunport_%s%d" % (tag, k + 1), origin=hinge, parent=guns)
            # open lid: hinged at the top, swung outwards and up
            ang = math.radians(55)
            lid_dir = norm(-v * math.cos(ang) + n * math.sin(ang))
            centre = hinge + lid_dir * 0.29
            axes = np.column_stack([u, np.cross(n, u) * 0 + norm(-lid_dir), norm(np.cross(u, -lid_dir))])
            add_cube(lid, "gunport_lid_%s%d" % (tag, k + 1), centre, axes, (0.6, 0.56, 0.08), "hull_mid")
            cb = Bone("cannon_%s%d" % (tag, k + 1), origin=p - n * 0.6 + v3(0, -0.1, 0), parent=guns)
            # the gun itself, run out (none at the port by the quarterdeck stairs: their first steps stand there)
            if z > gs.QD_STAIR_START + 0.4:
                g_cannon(cb, "cannon_%s%d" % (tag, k + 1), side, z, gs.GUNPORT_Y - 0.05, main_y, outer_x)
            # inner side of the bulwark
            pi_ = v3(side * (outer_x(z, gs.GUNPORT_Y) - 0.13), gs.GUNPORT_Y, z)
            add_cube(guns, "gunport_inner_%s%d" % (tag, k + 1), pi_, np.column_stack([u, v, v3(side, 0, 0)]),
                     (0.5, 0.48, 0.02), "gunport", stretch=True)

    # ---- poop house: the upper tier of the stern castle, its sides continuing the tumblehome of the hull,
    # rounded front corners, a curved back, a red frieze under the cornice and a cambered roof deck with a balustrade
    pf, pb = gs.POOP_FRONT, gs.POOP_BACK
    top_w = gs.POOP_WALL_TOP
    R = 0.42
    zbk = pb + 0.15     # the back wall curves forward towards its corners

    def p_cx(y):
        return castle_x(pf - R, y) - R

    def p_back_z(x, y):
        xb = castle_x(zbk, y)
        return pb + (zbk - pb) * min(1.0, (x / xb) ** 2)

    def perimeter(y, n_front=4, n_arc=4, n_side=4, n_back=8):
        """Outline of the poop house at height y, closed loop (front centre -> port side -> back -> starboard)."""
        pts = []
        cx = p_cx(y)
        for side in (1, -1):
            half = []
            for k in range(n_front):
                half.append(v3(side * cx * k / n_front, y, pf))
            for k in range(n_arc + 1):
                a = math.pi / 2 * k / n_arc
                half.append(v3(side * (cx + R * math.sin(a)), y, pf - R + R * math.cos(a)))
            for k in range(1, n_side + 1):
                z = pf - R + (zbk - (pf - R)) * k / n_side
                half.append(v3(side * castle_x(z, y), y, z))
            for k in range(1, n_back // 2 + 1):
                x = castle_x(zbk, y) * (1 - k / (n_back // 2))
                half.append(v3(side * x, y, p_back_z(x, y)))
            pts.append(half)
        port, stbd = pts
        return port + list(reversed(stbd[1:-1]))

    def offset(pts, d):
        c = sum(pts) / len(pts)
        out = []
        for i, p in enumerate(pts):
            t = pts[(i + 1) % len(pts)] - pts[i - 1]
            n_ = norm(v3(t[2], 0, -t[0]))
            if np.dot(n_, p - c) < 0:
                n_ = -n_
            out.append(p + n_ * d)
        return out

    def wall_ring(tag, y0, y1, reg, inner="hull_light", th=0.14, skip_front=False, d=0.0):
        A, B = offset(perimeter(y0), d), offset(perimeter(y1), d)
        c = sum(A) / len(A)
        for i in range(len(A)):
            j = (i + 1) % len(A)
            if skip_front and abs(A[i][2] - pf) < 1e-6 and abs(A[j][2] - pf) < 1e-6:
                continue
            mid = (A[i] + A[j]) / 2
            board(poop, "%s_%d" % (tag, i), A[i], B[i], A[j], B[j], th, reg, v3(mid[0] - c[0], 0, mid[2] - c[2]),
                  overlap=1.03, inner=inner)

    # walls: the front and back from the quarterdeck, the sides above the castle bulwark cap
    wall_ring("poop_wall_hi", 5.4, top_w, "wood_honey")
    wall_ring("poop_wall_mid", 4.55, 5.4, "wood_honey")
    wall_ring("poop_frieze", top_w - 0.3, top_w - 0.04, "red_paint", inner=None, th=0.04, d=0.03)
    # below the bulwark cap: front wall (to the bulwarks) and the back wall
    wl = castle_x(pf, 4.0) - 0.12
    add_cube(poop, "poop_front", (0, (qd_y + 4.56) / 2, pf - 0.08), EYE, (2 * wl, 4.56 - qd_y, 0.16),
             {"all": "wood_honey", "-3": "hull_light"})
    xs_b = np.linspace(-1, 1, 7)
    for j in range(6):
        P = lambda f, y: v3(f * (castle_x(zbk, y) - 0.12), y, p_back_z(f * (castle_x(zbk, y) - 0.12), y))  # noqa: E731
        board(poop, "poop_back_%d" % j, P(xs_b[j], qd_y), P(xs_b[j], 4.56), P(xs_b[j + 1], qd_y), P(xs_b[j + 1], 4.56), 0.14,
              "wood_honey", v3(0, 0, -1), overlap=1.03)
    # door with an arched gilded head, windows and pilasters on the front
    add_cube(poop, "poop_door", (0, qd_y + 0.95, pf + 0.01), EYE, (0.9, 1.8, 0.04), "door", stretch=True)
    arc = [v3(0.5 * math.cos(a), qd_y + 1.85 + 0.42 * math.sin(a), pf + 0.04) for a in np.linspace(0, math.pi, 7)]
    for j, (a, b) in enumerate(polyline(arc)):
        beam(poop, "poop_door_arch_%d" % j, a, b, 0.09, "gold", width=0.06, extend=0.03)
    add_cube(poop, "poop_door_tympanum", (0, qd_y + 2.0, pf + 0.015), EYE, (0.62, 0.26, 0.03), "carving", stretch=True)
    for side, sn in SIDES:
        add_cube(poop, "glow_poop_front_window_" + sn, (side * 1.7, qd_y + 1.45, pf + 0.01), EYE, (0.62, 1.1, 0.04), "arch_window",
                 stretch=True)
        add_cube(poop, "poop_front_window_sill_" + sn, (side * 1.7, qd_y + 0.86, pf + 0.04), EYE, (0.74, 0.08, 0.1), "wood_trim")
        add_cube(poop, "poop_front_pilaster_" + sn, (side * 0.75, (qd_y + top_w) / 2 - 0.15, pf + 0.02), EYE,
                 (0.2, top_w - qd_y - 0.3, 0.06), "pilaster", stretch=True)
        add_cube(poop, "poop_front_pilaster_out_" + sn, (side * (p_cx(5.4) - 0.12), (4.56 + top_w) / 2 - 0.15, pf + 0.02), EYE,
                 (0.16, top_w - 4.56 - 0.3, 0.05), "pilaster", stretch=True)
        # side windows (lit, arched) on the tumblehome
        u_hint = v3(0, 0, -side)
        for j, z in enumerate((-16.15, -15.05)):
            frame_decal(poop, "poop_window_%s%d" % (sn, j), castle_frame(z, 5.35, side), 0.5, 0.82, "arch_window", glow=True,
                        u_dir=u_hint)
        frame_decal(poop, "poop_pilaster_" + sn, castle_frame(-15.6, 5.3, side), 0.14, 1.3, "pilaster", out=0.012, u_dir=u_hint)
        # back windows
        xw = side * 1.05
        p_ = v3(xw, 5.3, p_back_z(xw, 5.3))
        u = norm(v3(1, 0, (p_back_z(xw + 0.02, 5.3) - p_back_z(xw - 0.02, 5.3)) / 0.04))
        Rw = np.column_stack([u, v3(0, 1, 0), np.cross(u, v3(0, 1, 0))])
        add_cube(poop, "glow_poop_back_window_" + sn, p_ - Rw[:, 2] * 0.02, Rw, (0.5, 0.85, 0.04), "arch_window", stretch=True)
    # cornice following the outline
    corn = offset(perimeter(top_w + 0.06), 0.07)
    for j, (a, b) in enumerate(polyline(corn, closed=True)):
        cap_rail(poop, "poop_cornice_%d" % j, a, b, 0.16, 0.22, "wood_trim", extend=0.04)

    # cambered roof deck
    roof_base, camber = top_w + 0.14, 0.26

    def roof_half(z):
        x = castle_x(z, top_w) + 0.06
        dz = z - (pf - R)
        if dz > 0:
            x = min(x, p_cx(top_w) + math.sqrt(max(0.0, (R + 0.06) ** 2 - dz * dz)))
        return x

    def roof_y(x, z):
        f = min(1.0, abs(x) / roof_half(z))
        return roof_base + camber * (1 - f * f)

    rz = [pb - 0.06, pb + 0.5, -16.0, -15.4, -14.9, pf - R, pf - R / 2, pf + 0.02]
    rs = np.linspace(-1, 1, 9)

    def RP(s, i):
        z = rz[i]
        if i == 0:
            z = p_back_z(s * castle_x(zbk, top_w), top_w) - 0.06
        x = s * roof_half(z)
        return v3(x, roof_y(x, z) + 0.0, z)
    for i in range(len(rz) - 1):
        for j in range(len(rs) - 1):
            board(poop, "roof_%d_%d" % (i, j), RP(rs[j], i), RP(rs[j + 1], i), RP(rs[j], i + 1), RP(rs[j + 1], i + 1), 0.12, "deck",
                  v3(0, 1, 0), overlap=1.03)
    # balustrade round the roof deck (round balusters, moulded gilded rail following the camber)
    path = offset(perimeter(top_w, n_front=6, n_arc=3, n_side=6, n_back=10), -0.12)
    rail_h = 0.5

    def on_roof(p, dy=0.0):
        return v3(p[0], roof_y(p[0], p[2]) + dy, p[2])
    for j, p in enumerate(path):
        round_bar(poop, "poop_baluster_%d" % j, on_roof(p, -0.02), on_roof(p, rail_h - 0.06), 0.08, "hull_light")
    for j, (a, b) in enumerate(polyline(path, closed=True)):
        cap_rail(poop, "poop_rail_%d" % j, on_roof(a, rail_h), on_roof(b, rail_h), 0.1, 0.13, "gold", extend=0.03)
    corners = []
    for side, sn in SIDES:
        a45 = v3(side * (p_cx(top_w) + R * 0.707), 0, pf - R + R * 0.707)
        bk = v3(side * castle_x(zbk, top_w), 0, zbk)
        for k, target in enumerate((a45, bk)):
            corners.append((sn, k, min(path, key=lambda q: (q[0] - target[0]) ** 2 + (q[2] - target[2]) ** 2)))
    for sn, k, p in corners:
        c = on_roof(p)
        round_bar(poop, "poop_corner_post_%s%d" % (sn, k), c - v3(0, 0.02, 0), c + v3(0, rail_h + 0.12, 0), 0.15, "dark_wood")
        lc = c + v3(0, rail_h + 0.42, 0)
        add_cube(lanterns, "roof_lantern_%s%d" % (sn, k), lc, EYE, (0.32, 0.44, 0.32), {"all": "lantern", "+2": "iron", "-2": "iron"},
                 stretch=True)
        add_cube(lanterns, "glow_roof_lantern_%s%d" % (sn, k), lc, EYE, (0.22, 0.32, 0.22), "glow", stretch=True)
    roof_top = roof_base + camber
    # stern lanterns: two on the transom corners, a big one on the poop roof
    for k, (x, y, z, s) in enumerate(((2.15, gs.QD_RAIL_Y + 0.2, -17.25, 1.0), (-2.15, gs.QD_RAIL_Y + 0.2, -17.25, 1.0),
                                      (0, roof_top - 0.02, pb + 0.75, 1.1))):
        round_bar(lanterns, "stern_lantern_pole_%d" % k, (x, y, z), (x, y + 0.5 * s, z), 0.09, "iron")
        if k < 2:
            # scrolled iron stay from the transom corner up to the lantern
            sc = bezier((x * 0.94, y - 0.75, z + 0.12), (x * 1.06, y - 0.2, z - 0.1), (x, y + 0.45 * s, z), 4)
            for j, (a, b) in enumerate(polyline(sc)):
                round_bar(lanterns, "stern_lantern_stay_%d_%d" % (k, j), a, b, 0.06, "iron", extend=0.02)
        g_great_lantern(lanterns, "stern_lantern_%d" % k, (x, y + 0.48 * s, z), s * 1.15)
    # bow lantern
    add_cube(lanterns, "bow_lantern", (0, gs.FC_RAIL_Y + 0.55, 17.3), EYE, (0.4, 0.55, 0.4), {"all": "lantern", "+2": "iron"}, stretch=True)
    add_cube(lanterns, "glow_bow_lantern", (0, gs.FC_RAIL_Y + 0.55, 17.3), EYE, (0.26, 0.4, 0.26), "glow", stretch=True)

    # ---- helm: wheel on a pedestal (bone helm_wheel turns with "steer")
    hub = v3(0, qd_y + 1.05, gs.HELM_Z)
    hz = gs.HELM_Z + 0.14
    disc(castle_aft, "helm_pedestal_base", (0, qd_y + 0.06, hz), (0, 1, 0), 0.3, 0.12, "gold", n=3)
    turned(castle_aft, "helm_pedestal", (0, qd_y + 0.1, hz), (0, hub[1] + 0.1, hz),
           [(0, 0.34), (0.12, 0.24), (0.3, 0.3), (0.42, 0.22), (0.85, 0.26), (0.95, 0.3), (1, 0)], "dark_wood")
    round_bar(castle_aft, "helm_axle", (0, hub[1], hz + 0.1), (0, hub[1], gs.HELM_Z - 0.12), 0.09, "iron")
    wheel = Bone("helm_wheel", origin=hub, parent=castle_aft)
    radius = 0.62
    zax = v3(0, 0, 1)
    disc(wheel, "helm_hub", hub, zax, 0.13, 0.22, "gold", n=3)
    disc(wheel, "helm_hub_boss", hub - zax * 0.13, zax, 0.07, 0.06, "gold")
    for k in range(8):
        a = 2 * math.pi * k / 8
        dvec = v3(math.cos(a), math.sin(a), 0)
        round_bar(wheel, "helm_spoke_%d" % k, hub + dvec * 0.1, hub + dvec * radius, 0.065, "hull_light")
        turned(wheel, "helm_handle_%d" % k, hub + dvec * (radius + 0.04), hub + dvec * (radius + 0.3),
               [(0, 0.06), (0.25, 0.09), (0.55, 0.065), (0.85, 0.08), (1, 0)], "hull_light")
    for k in range(16):
        a, a2 = 2 * math.pi * k / 16, 2 * math.pi * (k + 1) / 16
        p0 = hub + v3(math.cos(a), math.sin(a), 0) * radius
        p1 = hub + v3(math.cos(a2), math.sin(a2), 0) * radius
        beam(wheel, "helm_rim_%d" % k, p0, p1, 0.09, "dark_wood", width=0.1, up=v3(0, 0, 1), extend=0.02)
        q0 = hub + v3(math.cos(a), math.sin(a), 0) * (radius - 0.09)
        q1 = hub + v3(math.cos(a2), math.sin(a2), 0) * (radius - 0.09)
        beam(wheel, "helm_ring_%d" % k, q0, q1, 0.035, "gold", width=0.05, up=v3(0, 0, 1), extend=0.01)
    # binnacle beside the wheel: an eight-sided cabinet, the compass under a brass hood, two little lamps
    bn = v3(1.05, qd_y, gs.HELM_Z + 0.35)
    disc(castle_aft, "binnacle_foot", bn + v3(0, 0.05, 0), (0, 1, 0), 0.27, 0.1, "dark_wood")
    disc(castle_aft, "binnacle", bn + v3(0, 0.5, 0), (0, 1, 0), 0.22, 0.8, "wood_honey")
    disc(castle_aft, "binnacle_top", bn + v3(0, 0.92, 0), (0, 1, 0), 0.25, 0.06, "gold")
    disc(castle_aft, "binnacle_card", bn + v3(0, 0.96, 0), (0, 1, 0), 0.17, 0.02, {"all": "gold", "+2": "compass"})
    for s in (1, -1):
        add_cube(castle_aft, "glow_binnacle_lamp_%d" % (s > 0), bn + v3(s * 0.25, 0.8, 0), EYE, (0.08, 0.12, 0.08), "glow", stretch=True)
        add_cube(castle_aft, "binnacle_lamp_cap_%d" % (s > 0), bn + v3(s * 0.25, 0.88, 0), EYE, (0.1, 0.04, 0.1), "iron")

    # ---- rudder (bone "rudder" turns with "steer"), hinged on the transom
    rpivot = v3(0, 0.0, -gs.HALF_LENGTH - 0.12)
    rudder = Bone("rudder", origin=rpivot, parent=root)
    zf_r = -gs.HALF_LENGTH - 0.13
    y_top, y_bot = 0.6, -1.6

    def r_back(y):
        # the blade widens downwards in a smooth curve, its heel rounded off
        t = (y_top - y) / (y_top - y_bot)
        return zf_r - 0.4 - 0.56 * t ** 0.8 + 0.12 * max(0.0, t - 0.86) / 0.14

    bands = list(np.linspace(y_top, y_bot, 8))
    main_w = 0.3   # the thick main piece behind the stock; the blade thins aft of it
    for k in range(len(bands) - 1):
        y0, y1 = bands[k], bands[k + 1]
        board(rudder, "rudder_blade_%d" % k, v3(0.075, y0, zf_r - main_w + 0.02), v3(0.075, y0, r_back(y0)),
              v3(0.075, y1, zf_r - main_w + 0.02), v3(0.075, y1, r_back(y1)), 0.15, "hull_dark", v3(1, 0, 0), overlap=1.0)
        board(rudder, "rudder_main_%d" % k, v3(0.12, y0, zf_r), v3(0.12, y0, zf_r - main_w), v3(0.12, y1, zf_r),
              v3(0.12, y1, zf_r - main_w), 0.24, "dark_wood", v3(1, 0, 0), overlap=1.0)
    # rounded back edge and heel
    edge = [v3(0, y, r_back(y) + 0.03) for y in bands]
    for j, (a, b) in enumerate(polyline(edge)):
        round_bar(rudder, "rudder_edge_%d" % j, a, b, 0.17, "hull_dark", extend=0.03)
    round_bar(rudder, "rudder_heel", (0, y_bot + 0.03, zf_r - 0.05), (0, y_bot + 0.03, r_back(y_bot) + 0.06), 0.17, "hull_dark")
    round_bar(rudder, "rudder_stock", (0, -0.25, -gs.HALF_LENGTH - 0.16), (0, 0.75, -gs.HALF_LENGTH - 0.16), 0.24, "dark_wood")
    disc(rudder, "rudder_head", (0, 0.78, -gs.HALF_LENGTH - 0.16), (0, 1, 0), 0.15, 0.08, "gold", n=3)
    for k, y in enumerate((-1.15, -0.45, 0.25)):
        disc(rudder, "rudder_pintle_%d" % k, (0, y, -gs.HALF_LENGTH - 0.15), (0, 1, 0), 0.16, 0.1, "iron", n=3)
        for side in (1, -1):
            # iron straps over both faces: across the main piece, then along the thinner blade
            add_cube(rudder, "rudder_strap_%d_%d" % (k, side > 0), (side * 0.135, y, zf_r - main_w / 2 - 0.02), EYE,
                     (0.03, 0.09, main_w + 0.06), "iron")
            zb = r_back(y) + 0.25
            add_cube(rudder, "rudder_strap_tail_%d_%d" % (k, side > 0), (side * 0.09, y, (zf_r - main_w + zb) / 2), EYE,
                     (0.03, 0.08, abs(zb - zf_r + main_w) + 0.04), "iron")
            disc(rudder, "rudder_bolt_%d_%d" % (k, side > 0), (side * 0.16, y, zf_r - main_w + 0.06), (side, 0, 0), 0.035, 0.03,
                 "iron")

    # ---- bow: stem post, beakhead, figurehead, bowsprit, anchors
    stem_pts = []
    for j in range(7):
        t = j / 6
        z = 17.5 + 0.8 * t ** 1.6
        y = gs.keel_y(17.5) - 0.1 + (gs.FC_RAIL_Y + 0.2 - gs.keel_y(17.5)) * t
        stem_pts.append(v3(0, y, z))
    for j in range(len(stem_pts) - 1):
        beam(bow, "stem_%d" % j, stem_pts[j], stem_pts[j + 1], 0.4, "dark_wood", width=0.5, extend=0.1)
    beak_z0, beak_z1 = 17.6, 20.0
    # knee of the head: a curved cutwater growing out of the stem under the beakhead
    knee = bezier((0, 0.35, 17.62), (0, 1.25, 19.45), (0, 2.42, 20.05), 6)
    for j, (a, b) in enumerate(polyline(knee)):
        beam(bow, "beak_knee_%d" % j, a, b, 0.62 - 0.05 * j, "dark_wood", width=0.34 - 0.02 * j, extend=0.06, up=v3(0, 0, 1))
    # beakhead platform (grating), tapering forward
    plat = [v3(0, 2.38, beak_z0), v3(0, 2.46, 18.4), v3(0, 2.54, 19.2), v3(0, 2.6, beak_z1)]
    for j, (a, b) in enumerate(polyline(plat)):
        beam(bow, "beakhead_%d" % j, a, b, 0.16, {"all": "wood_honey", "+2": "grating"}, width=1.0 - 0.17 * j, extend=0.03)
    for side, sn in SIDES:
        # head rails sweeping from the bow down and forward to the figurehead, with their timbers
        z0 = 16.5
        up_rail = bezier((side * (hw(z0) + 0.04), 3.75, z0), (side * 0.85, 2.7, 18.3), (side * 0.16, 3.05, 19.85), 6)
        low_rail = bezier((side * (hw(z0 + 0.1) + 0.04), 3.1, z0 + 0.1), (side * 0.75, 2.3, 18.2), (side * 0.22, 2.68, 19.55), 5)
        for j, (a, b) in enumerate(polyline(up_rail)):
            round_bar(bow, "head_rail_%s%d" % (sn, j), a, b, 0.11, "gold", extend=0.03)
        for j, (a, b) in enumerate(polyline(low_rail)):
            round_bar(bow, "head_rail_low_%s%d" % (sn, j), a, b, 0.09, "wood_trim", extend=0.03)
        for j in (2, 3, 4):
            p = up_rail[j]
            round_bar(bow, "head_timber_%s%d" % (sn, j), v3(p[0] * 0.8, 2.45, p[2]), p, 0.07, "wood_trim")
        # cheek knees: curved mouldings along the bow, rising into the knee of the head
        for k, (y0, reg) in enumerate(((2.05, "gold"), (1.55, "wood_trim"))):
            pts = [v3(side * (outer_x(z, y0) + 0.05), y0 + 0.3 * ((z - 15.2) / 2.5) ** 2, z) for z in (15.2, 16.0, 16.7, 17.25)]
            pts.append(v3(side * 0.2, y0 + 0.42, 17.75))
            for j, (a, b) in enumerate(polyline(pts)):
                round_bar(bow, "cheek_%s%d_%d" % (sn, k, j), a, b, 0.11, reg, extend=0.03)
    lion = Bone("figurehead", origin=(0, 2.6, beak_z1), parent=bow)
    lion_figurehead(lion, (0, 2.75, beak_z1 + 0.2), 0.55)
    sprit_a, sprit_b = v3(0, 3.9, 16.4), v3(0, 6.9, 24.6)
    round_bar(bow, "bowsprit", sprit_a, sprit_b, 0.4, "mast")
    beam(bow, "bowsprit_cap", sprit_b - norm(sprit_b - sprit_a) * 0.15, sprit_b + norm(sprit_b - sprit_a) * 0.1, 0.48, "dark_wood")
    jib_boom = sprit_b + norm(sprit_b - sprit_a) * 0.05
    beam(bow, "bowsprit_staff", jib_boom, jib_boom + v3(0, 0.9, 0), 0.08, "dark_wood")
    for side, sn in SIDES:
        z = 14.6
        x = side * (hw(z) + 0.15)
        g_anchor(bow, "anchor_" + sn, (x, 3.3, z), (x, 1.6, z - 0.1), (0, 0, 1))
        disc(bow, "hawse_" + sn, side_frame(16.0, 2.5, side)[0] + v3(side * 0.03, 0, 0), (side, 0, 0), 0.14, 0.06, "iron")

    # ---- masts, tops, yards
    def mast(name, z, foot, top, lower_top, thick):
        mb = Bone(name, origin=(0, foot, z), parent=root)
        round_bar(mb, name + "_lower", (0, foot - 0.2, z), (0, lower_top + 0.6, z), thick, "mast")
        round_bar(mb, name + "_upper", (0, lower_top - 0.4, z), (0, top, z), thick * 0.62, "mast")
        disc(mb, name + "_partners", (0, foot + 0.1, z), (0, 1, 0), (thick + 0.35) / 2, 0.2, "dark_wood", n=3)
        disc(mb, name + "_coat", (0, foot + 0.24, z), (0, 1, 0), thick / 2 + 0.07, 0.1, "gold", n=3)
        disc(mb, name + "_cap", (0, top - 0.08, z), (0, 1, 0), (thick * 0.62 + 0.15) / 2, 0.22, "gold", n=3)
        # wooldings: rope bands round the lower mast
        for k, y in enumerate(np.linspace(foot + 1.6, lower_top - 1.2, 4)):
            round_bar(mb, "%s_woolding_%d" % (name, k), (0, y - 0.07, z), (0, y + 0.07, z), thick * 1.1, "rope")
        # round fighting top: trestle and cross trees, a platform of radial boards, a painted rim with a gilt cap,
        # and the futtock shrouds under it
        r = 0.95 + thick
        for s in (1, -1):
            beam(mb, "%s_trestle_%d" % (name, s > 0), (s * thick * 0.6, lower_top - 0.2, z - r * 0.9),
                 (s * thick * 0.6, lower_top - 0.2, z + r * 0.9), 0.16, "dark_wood", width=0.14)
            beam(mb, "%s_crosstree_%d" % (name, s > 0), (-r * 0.9, lower_top - 0.13, z + s * r * 0.35),
                 (r * 0.9, lower_top - 0.13, z + s * r * 0.35), 0.1, "dark_wood", width=0.12)
        n_ = 12
        ri = thick * 0.6
        for k in range(n_):
            a, a2 = 2 * math.pi * k / n_, 2 * math.pi * (k + 1) / n_
            P = lambda rr, aa: v3(math.cos(aa) * rr, lower_top, z + math.sin(aa) * rr)  # noqa: E731
            board(mb, "%s_top_%d" % (name, k), P(ri, a), P(r, a), P(ri, a2), P(r, a2), 0.1, "deck", v3(0, 1, 0), overlap=1.02,
                  inner="dark_wood")
        n_ = 16
        for k in range(n_):
            a, a2 = 2 * math.pi * k / n_, 2 * math.pi * (k + 1) / n_
            p0 = v3(math.cos(a) * r, lower_top + 0.3, z + math.sin(a) * r)
            p1 = v3(math.cos(a2) * r, lower_top + 0.3, z + math.sin(a2) * r)
            o = v3(math.cos((a + a2) / 2), 0, math.sin((a + a2) / 2))
            board(mb, "%s_top_rim_%d" % (name, k), p0 - v3(0, 0.4, 0), p0, p1 - v3(0, 0.4, 0), p1, 0.06, "red_paint", o,
                  overlap=1.06, inner="dark_wood")
            beam(mb, "%s_top_cap_%d" % (name, k), p0 + v3(0, 0.03, 0) - o * 0.01, p1 + v3(0, 0.03, 0) - o * 0.01, 0.07, "gold",
                 width=0.12, extend=0.03)
            if k % 2 == 0:
                beam(mb, "%s_top_band_%d" % (name, k), p0 - v3(0, 0.33, 0) + o * 0.035, p1 - v3(0, 0.33, 0) + o * 0.035, 0.05, "gold",
                     width=0.02, extend=0.0)
        for k in range(4):
            a = 2 * math.pi * (k + 0.5) / 4
            o = v3(math.cos(a), 0, math.sin(a))
            beam(mb, "%s_futtock_%d" % (name, k), o * (r * 0.92) + v3(0, lower_top - 0.05, z), o * (thick * 0.55) + v3(0, lower_top - 1.6, z),
                 0.045, "rope")
        return mb

    m_main = mast("mainmast", gs.MAIN_MAST_Z, main_y, gs.MAIN_MAST_TOP, 15.2, 0.62)
    m_fore = mast("foremast", gs.FORE_MAST_Z, fc_y, gs.FORE_MAST_TOP, 13.0, 0.52)
    m_mizzen = Bone("mizzen", origin=(0, main_y, gs.MIZZEN_Z), parent=root)
    round_bar(m_mizzen, "mizzen_mast", (0, main_y, gs.MIZZEN_Z), (0, gs.MIZZEN_TOP, gs.MIZZEN_Z), 0.42, "mast")
    disc(m_mizzen, "mizzen_partners", (0, qd_y + 0.1, gs.MIZZEN_Z), (0, 1, 0), 0.4, 0.2, "dark_wood", n=3)
    disc(m_mizzen, "mizzen_coat", (0, qd_y + 0.24, gs.MIZZEN_Z), (0, 1, 0), 0.28, 0.1, "gold", n=3)
    disc(m_mizzen, "mizzen_cap", (0, gs.MIZZEN_TOP - 0.08, gs.MIZZEN_Z), (0, 1, 0), 0.28, 0.22, "gold", n=3)
    # gilt collars where the mizzen passes through the great cabin
    disc(m_mizzen, "mizzen_cabin_foot", (0, main_y + 0.06, gs.MIZZEN_Z), (0, 1, 0), 0.32, 0.12, "gold", n=3)
    disc(m_mizzen, "mizzen_cabin_head", (0, qd_y - gs.QUARTERDECK_SLAB - 0.06, gs.MIZZEN_Z), (0, 1, 0), 0.32, 0.12, "gold", n=3)
    for k, y in enumerate((5.6, 8.0, 10.4)):
        round_bar(m_mizzen, "mizzen_woolding_%d" % k, (0, y - 0.06, gs.MIZZEN_Z), (0, y + 0.06, gs.MIZZEN_Z), 0.47, "rope")

    def yard(mb, name, z, y, half):
        round_bar(mb, name, (-half, y, z + 0.38), (half, y, z + 0.38), 0.22, "mast", extend=0.1)
        add_cube(mb, name + "_sling", (0, y, z + 0.3), EYE, (0.4, 0.34, 0.34), "rope")
        # furled canvas bundle along the yard (seen when the sail is struck)
        beam(mb, name + "_roll", (-half * 0.92, y - 0.2, z + 0.42), (half * 0.92, y - 0.2, z + 0.42), 0.24, "cloth_roll")

    sails_info = []

    def square_sail(mb, name, z, y_top, half_top, half_bottom, height, region, depth):
        # yard and sail hang in a bone turned around the mast: the yards are braced round, so the
        # bellied sails show their curve from the side as on the reference pictures
        br = Bone("brace_" + name, origin=(0, y_top, z), parent=mb)
        yard(br, name + "_yard", z, y_top, half_top + 0.35)
        sb = Bone("sail_" + name, origin=(0, y_top, z + 0.42), parent=br)
        fine = height > 7.5
        g_sail(sb, name, v3(0, y_top - 0.12, z + 0.45), v3(1, 0, 0), v3(0, -1, 0), v3(0, 0, 1), half_top, half_bottom,
               height, depth * 2.1, region, nx=12 if fine else 10, ny=15 if fine else 12, round_=0.8, foot=0.09, ease=1.15)
        br.rot = ry(BRACE)
        sails_info.append((sb, False))
        return sb

    square_sail(m_main, "main_course", gs.MAIN_MAST_Z, 14.1, 4.6, 5.3, 8.9, "course", 1.25)
    square_sail(m_main, "main_topsail", gs.MAIN_MAST_Z, 23.4, 2.9, 4.1, 6.6, "topsail", 0.9)
    square_sail(m_fore, "fore_course", gs.FORE_MAST_Z, 12.2, 3.8, 4.5, 6.0, "course", 1.0)
    square_sail(m_fore, "fore_topsail", gs.FORE_MAST_Z, 19.9, 2.4, 3.3, 5.4, "topsail", 0.75)

    # mizzen lateen yard and sail
    lat_fore, lat_aft = v3(0.32, 8.0, -8.0), v3(0.32, 16.6, -17.4)
    round_bar(m_mizzen, "lateen_yard", lat_fore - norm(lat_aft - lat_fore) * 0.3, lat_aft, 0.2, "mast")
    beam(m_mizzen, "lateen_roll", lat_fore + v3(0.05, -0.2, 0) + norm(lat_aft - lat_fore) * 0.8,
         lat_aft + v3(0.05, -0.2, 0) - norm(lat_aft - lat_fore) * 0.4, 0.24, "cloth_roll")
    lat_sail = Bone("sail_mizzen", origin=tuple((lat_fore + lat_aft) / 2), parent=m_mizzen)
    lateen_tri = g_tri_sail(lat_sail, "mizzen_lateen", lat_aft + v3(0.08, -0.12, 0.05), lat_fore + v3(0.08, -0.12, 0),
                            v3(0.4, 8.0, -16.4), 0.85, v3(1, 0, 0), "lateen", nx=8, ny=12, round_=0.45)
    sails_info.append((lat_sail, True))

    # jibs on the stays to the bowsprit
    beam(bow, "jib_roll", sprit_a + (sprit_b - sprit_a) * 0.5 + v3(0, 0.25, 0), sprit_b + v3(0, 0.22, -0.3), 0.2, "cloth_roll")
    jib = Bone("jib", origin=tuple(sprit_b), parent=root)
    fore_head = v3(0, gs.FORE_MAST_TOP - 0.5, gs.FORE_MAST_Z)
    stay_top = sprit_b + (fore_head - sprit_b) * 0.62
    outer_clew = jib_clew(stay_top, sprit_b, v3(0.05, 6.6, 19.2))
    jib_tri = g_tri_sail(jib, "jib_outer", stay_top + v3(0.0, -0.05, -0.06), sprit_b + v3(0, 0.05, -0.12),
                         outer_clew, 0.6, v3(1, 0, 0), "jib", nx=7, ny=9, round_=0.45)
    fore_low = v3(0, 13.0, gs.FORE_MAST_Z)
    mid_sprit = sprit_a + (sprit_b - sprit_a) * 0.55
    st2 = mid_sprit + (fore_low - mid_sprit) * 0.62
    g_tri_sail(jib, "jib_inner", st2 + v3(0.0, -0.05, -0.06), mid_sprit + v3(0, 0.05, -0.1),
               jib_clew(st2, mid_sprit, v3(0.05, 5.0, 16.2)), 0.5, v3(1, 0, 0), "jib", nx=7, ny=9, round_=0.45)
    sails_info.append((jib, True))
    sprit_yard = sprit_a + (sprit_b - sprit_a) * 0.72
    round_bar(bow, "spritsail_yard", sprit_yard + v3(-2.3, -0.25, 0), sprit_yard + v3(2.3, -0.25, 0), 0.16, "mast", extend=0.08)
    beam(bow, "spritsail_roll", sprit_yard + v3(-1.9, -0.45, 0.05), sprit_yard + v3(1.9, -0.45, 0.05), 0.22, "cloth_roll")
    sprit_sail = Bone("sail_sprit", origin=tuple(sprit_yard + v3(0, -0.3, 0)), parent=bow)
    g_sail(sprit_sail, "spritsail", sprit_yard + v3(0, -0.36, 0.12), v3(1, 0, 0), v3(0, -1, 0), v3(0, 0, 1), 2.1, 2.4, 2.3, 0.8,
           "topsail", nx=7, ny=7, round_=0.7, foot=0.08)
    sails_info.append((sprit_sail, False))

    # ---- flags (texture #1): masthead flags, main pennant, stern ensign
    def flag(parent, name, root_pt, w, h, region="flag", n=3):
        """Flag in two bones (the animation swings the root half and the fly), each half made of n strips
        that follow a soft wave, so the cloth ripples instead of standing as a flat board."""
        fb = Bone("flag_" + name, origin=tuple(root_pt), parent=parent)
        tip_root = root_pt + v3(0, 0, -w / 2)
        ft = Bone("flag_%s_tip" % name, origin=tuple(tip_root), parent=fb)
        amp = min(0.16, 0.07 * w)

        def P(s):
            # zero at the staff and at the hinge of the two halves
            return root_pt + v3(amp * math.sin(2 * math.pi * s) * (0.35 + s), 0, -w * s)
        for half, bone in enumerate((fb, ft)):
            for k in range(n):
                s0, s1 = (half + k / n) / 2, (half + (k + 1) / n) / 2
                a, b = P(s0), P(s1)
                d = norm(b - a)
                axes = np.column_stack([np.cross(v3(0, 1, 0), d), v3(0, 1, 0), d])
                c = add_cube(bone, "flag_%s_%s%d" % (name, "ab"[half], k), (a + b) / 2 + v3(0, -h / 2, 0), axes,
                             (0.03, h, np.linalg.norm(b - a) + 0.015), {"all": None, "+1": region, "-1": region},
                             stretch=True, u_dir=v3(0, 0, -1), v_dir=v3(0, -1, 0))
                set_sub(c, (s0, 0, s1, 1), faces=("west", "east"))
        return fb

    for mb, name, z, top in ((m_main, "main", gs.MAIN_MAST_Z, gs.MAIN_MAST_TOP), (m_fore, "fore", gs.FORE_MAST_Z, gs.FORE_MAST_TOP),
                             (m_mizzen, "mizzen", gs.MIZZEN_Z, gs.MIZZEN_TOP)):
        beam(mb, name + "_flagpole", (0, top, z), (0, top + 1.3, z), 0.1, "dark_wood")
        if name == "main":
            # long swallow-tail pennant
            fb = flag(mb, name, v3(0, top + 1.2, z), 4.2, 0.55, region="pennant")
        else:
            flag(mb, name, v3(0, top + 1.2, z), 1.9, 1.15)
    staff_base = v3(0, roof_top - 0.05, gs.POOP_BACK + 0.25)
    beam(castle_aft, "ensign_staff", staff_base, staff_base + v3(0, 3.2, -0.6), 0.12, "dark_wood")
    flag(castle_aft, "stern", staff_base + v3(0, 3.1, -0.65), 2.7, 1.7)

    # ---- rigging
    rope = 0.055
    rig = []

    def deadeye(z, side, y=None):
        y = gs.rail_y(z) if y is None else y
        return v3(side * (0.98 * hw(z) + 0.12), y - 0.1, z)

    CHANNEL_ZM = {"main": 0.9, "fore": 12.2, "mizzen": -12.6}

    def shroud_foot(z, side, tag):
        """Upper deadeye of a lower shroud, standing on the outer edge of its channel."""
        ych = gs.rail_y(CHANNEL_ZM[tag]) - 0.22
        return v3(side * (castle_x(z, ych) + 0.3), ych + 0.5, z)

    for side, sn in SIDES:
        for k, z in enumerate((-0.6, 0.4, 1.4, 2.4)):
            rig.append(("main_shroud_%s%d" % (sn, k), v3(side * 0.9, 15.15, gs.MAIN_MAST_Z), shroud_foot(z, side, "main")))
        for k, z in enumerate((11.4, 12.2, 13.0)):
            rig.append(("fore_shroud_%s%d" % (sn, k), v3(side * 0.8, 12.95, gs.FORE_MAST_Z), shroud_foot(z, side, "fore")))
        for k, z in enumerate((-12.0, -13.2)):
            rig.append(("mizzen_shroud_%s%d" % (sn, k), v3(side * 0.2, 13.0, gs.MIZZEN_Z), shroud_foot(z, side, "mizzen")))
        for k in range(2):
            rig.append(("main_topshroud_%s%d" % (sn, k), v3(side * 0.25, gs.MAIN_MAST_TOP - 1.2, gs.MAIN_MAST_Z),
                        v3(side * 1.4, 15.4, gs.MAIN_MAST_Z + (k - 0.5) * 0.9)))
            rig.append(("fore_topshroud_%s%d" % (sn, k), v3(side * 0.2, gs.FORE_MAST_TOP - 1.0, gs.FORE_MAST_Z),
                        v3(side * 1.25, 13.2, gs.FORE_MAST_Z + (k - 0.5) * 0.8)))
        # sheets from the course clews to the rail, braces from the yard arms aft
        mz, fz = gs.MAIN_MAST_Z, gs.FORE_MAST_Z
        rig.append(("main_sheet_" + sn, braced((side * 5.2, 5.6, mz + 1.6), mz), deadeye(-3.0, side)))
        rig.append(("main_brace_" + sn, braced((side * 4.9, 14.1, mz + 0.4), mz), deadeye(-9.5, side, gs.QD_RAIL_Y)))
        rig.append(("main_topbrace_" + sn, braced((side * 3.2, 23.4, mz + 0.4), mz), v3(side * 0.2, 15.0, gs.MIZZEN_Z)))
        rig.append(("fore_sheet_" + sn, braced((side * 4.4, 6.6, fz + 1.3), fz), deadeye(8.6, side)))
        rig.append(("fore_brace_" + sn, braced((side * 4.1, 12.2, fz + 0.4), fz), v3(side * 0.6, 14.4, mz)))
    rig += [
        ("main_stay", v3(0, 15.0, gs.MAIN_MAST_Z + 0.3), v3(0, fc_y + 0.4, gs.FORE_MAST_Z - 0.4)),
        ("main_topstay", v3(0, gs.MAIN_MAST_TOP - 0.6, gs.MAIN_MAST_Z), v3(0, 13.2, gs.FORE_MAST_Z)),
        ("fore_stay", v3(0, 12.9, gs.FORE_MAST_Z + 0.2), mid_sprit),
        ("fore_topstay", fore_head, sprit_b),
        ("mizzen_stay", v3(0, gs.MIZZEN_TOP - 0.4, gs.MIZZEN_Z), v3(0, 9.5, gs.MAIN_MAST_Z - 0.3)),
        ("mizzen_backstay", v3(0, gs.MIZZEN_TOP - 0.6, gs.MIZZEN_Z), v3(0, gs.QD_RAIL_Y + 0.2, -17.3)),
        ("lateen_halyard", v3(0.2, gs.MIZZEN_TOP - 0.4, gs.MIZZEN_Z), lat_fore + (lat_aft - lat_fore) * 0.5),
        ("lateen_sheet", v3(0.4, 8.0, -16.4), v3(0.4, gs.QD_RAIL_Y + 0.1, -17.2)),
        ("jib_sheet", outer_clew, v3(0.4, gs.FC_RAIL_Y, 15.9)),
        ("bobstay", sprit_b - v3(0, 0.15, 0.3), v3(0, 1.0, 18.0)),
    ]
    for name, a, b in rig:
        beam(ropes, "rope_" + name, a, b, rope, "rope")
        if "shroud" in name and "top" not in name:
            # pair of round deadeyes set up with a lanyard, the lower one held by a chain plate bolted to the hull
            side = 1 if b[0] > 0 else -1
            ax = v3(side, 0, 0)
            low = b - v3(0, 0.36, 0)
            disc(ropes, "deadeye_" + name, b, ax, 0.11, 0.08, "dark_wood")
            disc(ropes, "deadeye_low_" + name, low, ax, 0.11, 0.08, "dark_wood")
            for j, dz in enumerate((-0.045, 0.045)):
                beam(ropes, "lanyard_%s_%d" % (name, j), b + v3(0, -0.06, dz), low + v3(0, 0.06, -dz), 0.03, "rope")
            yb = low[1] - 1.0
            pb = v3(side * (castle_x(b[2], yb) + 0.04), yb, b[2])
            beam(ropes, "chain_" + name, low - v3(0, 0.08, 0), pb, 0.05, "iron", up=ax)
            disc(ropes, "chain_bolt_" + name, pb, ax, 0.05, 0.05, "iron")
    # ratlines across the main and fore shrouds
    for side, sn in SIDES:
        for mast_tag, top_y, z_top, z0, z1, foot_y in (("main", 15.15, gs.MAIN_MAST_Z, -0.6, 2.4, None),
                                                      ("fore", 12.95, gs.FORE_MAST_Z, 11.4, 13.0, None)):
            top_pt = v3(side * 0.9, top_y, z_top)
            fa, fb_ = shroud_foot(z0, side, mast_tag), shroud_foot(z1, side, mast_tag)
            for k in range(1, 9):
                t = k / 9.5
                pa = fa + (top_pt - fa) * t
                pb = fb_ + (top_pt - fb_) * t
                beam(ropes, "ratline_%s_%s%d" % (mast_tag, sn, k), pa, pb, 0.04, "rope")
    return root, lateen_tri, jib_tri, sails_info


# ---------------------------------------------------------------- animations
def build_animations(root, sails_info):
    kf, rot_kf, animation, find = gg.kf, gg.rot_kf, gg.animation, gg.find
    anims = []
    # wind in the sails: the belly breathes (scale along the billow) and the cloth sways
    tracks = []
    for k, (b, side_billow) in enumerate(sails_info):
        ph = 0.37 * k
        if side_billow:
            sc = [kf("scale", t, (s, 1, 1), "catmullrom") for t, s in ((0, 1.0), (0.9, 1.18), (1.8, 0.92), (2.7, 1.1), (3.6, 1.0))]
            rt = [rot_kf(t, (0, 0, a), "catmullrom") for t, a in ((0, 0), (1.2, 1.2), (2.4, -0.8), (3.6, 0))]
        else:
            sc = [kf("scale", t, (1, 1, s), "catmullrom") for t, s in ((0, 1.0), (0.9 + ph * 0.1, 1.16), (1.8, 0.9), (2.7, 1.08), (3.6, 1.0))]
            rt = [rot_kf(t, (a, 0, 0), "catmullrom") for t, a in ((0, 0), (1.2, -1.6), (2.4, 0.8), (3.6, 0))]
        tracks.append((b, sc + rt))
    anims.append(animation("sail_wind", 3.6, "loop", tracks))
    # furl: sails gathered up to their yards (time 0 = set, 1 = furled)
    tracks = []
    for b, side_billow in sails_info:
        if side_billow:
            tracks.append((b, [kf("scale", 0.0, (1, 1, 1)), kf("scale", 1.0, (0, 0, 0))]))
        else:
            tracks.append((b, [kf("scale", 0.0, (1, 1, 1)), kf("scale", 1.0, (0.95, 0, 0))]))
    anims.append(animation("sail_furl", 1.0, "hold", tracks))
    # steer: 0 = full port helm, 1 = centre, 2 = full starboard
    wheel, rudder = find(root, "helm_wheel"), find(root, "rudder")
    anims.append(animation("steer", 2.0, "hold", [
        (wheel, [rot_kf(0.0, (0, 0, -150)), rot_kf(1.0, (0, 0, 0)), rot_kf(2.0, (0, 0, 150))]),
        (rudder, [rot_kf(0.0, (0, -30, 0)), rot_kf(1.0, (0, 0, 0)), rot_kf(2.0, (0, 30, 0))])]))
    # flags
    tracks = []
    for k, name in enumerate(("main", "fore", "mizzen", "stern")):
        f, ft = find(root, "flag_" + name), find(root, "flag_%s_tip" % name)
        a = 8 if name != "main" else 12
        sh = 0.15 * k
        tracks.append((f, [rot_kf(0 + sh, (0, a, 0), "catmullrom"), rot_kf(0.6 + sh, (0, -a, 0), "catmullrom"),
                           rot_kf(1.2 + sh, (0, a, 0), "catmullrom")]))
        tracks.append((ft, [rot_kf(0 + sh, (0, -2 * a, 0), "catmullrom"), rot_kf(0.6 + sh, (0, 2 * a, 0), "catmullrom"),
                            rot_kf(1.2 + sh, (0, -2 * a, 0), "catmullrom")]))
    for b, kfs in tracks:
        # keep keyframe times inside the loop
        for k in kfs:
            k["time"] = round(k["time"] % 1.2 if k["time"] > 1.2 else k["time"], 4)
        kfs.sort(key=lambda k: k["time"])
    anims.append(animation("flag_wave", 1.2, "loop", tracks))
    return anims


# ---------------------------------------------------------------- export
def face_uv(cube, bbface, spec, seed):
    tex, u0, v0, rw, rh = REGIONS[spec["region"]]
    normal, udir, vdir = gg.FACE_AXES[bbface]
    size_bb = cube.size
    du = abs(np.dot(udir, size_bb))
    dv = abs(np.dot(vdir, size_bb))
    sub = spec.get("sub")
    if sub is not None:
        uv = [u0 + sub[0] * rw, v0 + sub[1] * rh, u0 + sub[2] * rw, v0 + sub[3] * rh]
    elif spec["stretch"]:
        uv = [u0, v0, u0 + rw, v0 + rh]
    else:
        su = min(rw, max(1, round(du * 16 * spec["density"])))
        sv = min(rh, max(1, round(dv * 16 * spec["density"])))
        ou = (seed * 7) % max(1, rw - su + 1)
        ov = ((seed // 3) * 4) % max(1, rh - sv + 1)
        ov -= ov % 4
        uv = [u0 + ou, v0 + ov, u0 + ou + su, v0 + ov + sv]
    Rbb = gg.to_bb_rot(cube.axes)
    for idx, hint, axis in ((0, spec["u_dir"], udir), (1, spec["v_dir"], vdir)):
        if hint is None:
            continue
        world_axis = gg.M @ (Rbb @ axis)
        if np.dot(world_axis, hint) < 0:
            uv[idx], uv[idx + 2] = uv[idx + 2], uv[idx]
    return [round(x, 4) for x in uv], tex


def texture_entry(name, size, png, rel, default_name="galleon.png"):
    return {
        "path": "", "name": name, "folder": "entity", "namespace": "medievalships", "id": str(len(name) % 2),
        "group": "", "width": size, "height": size, "uv_width": size, "uv_height": size,
        "particle": False, "use_as_default": name == default_name, "layers_enabled": False, "sync_to_project": "",
        "render_mode": "default", "render_sides": "auto", "frame_time": 1, "frame_order_type": "loop",
        "frame_order": "", "frame_interpolate": False, "visible": True, "internal": True, "saved": True,
        "uuid": new_uuid(), "relative_path": "../src/main/resources/assets/medievalships/textures/entity/" + name,
        "source": "data:image/png;base64," + base64.b64encode(png).decode()}


def export(root, anims, textures, out_paths, name="galleon", visible_box=(40, 32, 0), extra=None):
    import lanterns  # every ship gets the same lit-glass lanterns
    print("lanterns: %d" % lanterns.convert(root))
    import rope_follow  # sheets stay on the clews when the sails are furled
    print("ropes following the furled sails: %d" % rope_follow.follow(root, anims))
    import zfight  # coplanar faces would flicker in game
    zfight.fix(root)
    elements = []

    def group_json(b):
        children = []
        for c in b.cubes:
            Rbb = gg.to_bb_rot(c.axes)
            euler = gg.matrix_to_euler_zyx(Rbb)
            center = gg.to_bb_point(c.center)
            half = c.size * 8.0
            frm = [round(center[k] - half[k], 4) for k in range(3)]
            to = [round(center[k] + half[k], 4) for k in range(3)]
            faces = {}
            for bbface, spec in c.faces.items():
                if spec is None:
                    faces[bbface] = {"uv": [0, 0, 0, 0], "texture": None}
                else:
                    seed = zlib.crc32((c.name + bbface).encode()) % 9973
                    uv, tex = face_uv(c, bbface, spec, seed)
                    faces[bbface] = {"uv": uv, "texture": tex}
            el = {"name": c.name, "box_uv": False, "rescale": False, "locked": False,
                  "render_order": "default", "allow_mirror_modeling": True,
                  "from": frm, "to": to, "autouv": 0, "color": 0, "origin": center,
                  "faces": faces, "type": "cube", "uuid": c.uuid}
            if any(abs(x) > 1e-4 for x in euler):
                el["rotation"] = euler
            elements.append(el)
            children.append(c.uuid)
        for ch in b.children:
            children.append(group_json(ch))
        g = {"name": b.name, "origin": gg.to_bb_point(b.origin), "color": 0, "uuid": b.uuid, "export": True,
             "mirror_uv": False, "isOpen": False, "locked": False, "visibility": True, "autouv": 0,
             "children": children}
        e = gg.matrix_to_euler_zyx(gg.to_bb_rot(b.rot))
        if any(abs(x) > 1e-4 for x in e):
            g["rotation"] = e
        return g

    outliner = [group_json(root)]
    model = {
        "meta": {"format_version": "4.10", "model_format": "free", "box_uv": False},
        "name": name,
        "model_identifier": name,
        "visible_box": list(visible_box),
        "variable_placeholders": "",
        "variable_placeholder_buttons": [],
        "timeline_setups": [],
        "unhandled_root_fields": {},
        "resolution": {"width": SIZE, "height": SIZE},
        "elements": elements,
        "outliner": outliner,
        "textures": textures,
        "animations": anims,
    }
    model.update(extra or {})
    for p in out_paths:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w") as f:
            json_dump(model, f, compact="resources" in p)
    return model


def json_dump(model, f, compact):
    import json
    json.dump(model, f, separators=(",", ":") if compact else (", ", ": "), indent=None if compact else 1)


def main():
    root, lateen_tri, jib_tri, sails_info = build()
    anims = build_animations(root, sails_info)
    tex_dir = os.path.join(ROOT, "src/main/resources/assets/medievalships/textures")
    tex_path = os.path.join(tex_dir, "entity/galleon.png")
    flag_path = os.path.join(tex_dir, "entity/galleon_flag.png")
    make_textures(tex_path, flag_path, lateen_tri, jib_tri)
    make_item_icon(os.path.join(tex_dir, "item/galleon.png"))
    with open(tex_path, "rb") as f:
        png = f.read()
    with open(flag_path, "rb") as f:
        flag_png = f.read()
    textures = [texture_entry("galleon.png", SIZE, png, "entity"), texture_entry("galleon_flag.png", FLAG_SIZE, flag_png, "entity")]
    textures[0]["id"], textures[1]["id"] = "0", "1"
    model = export(root, anims, textures, [
        os.path.join(ROOT, "blockbench/galleon.bbmodel"),
        os.path.join(ROOT, "src/main/resources/assets/medievalships/models/entity/galleon.bbmodel"),
    ])
    n_groups = [0]

    def count(g):
        n_groups[0] += 1
        for c in g["children"]:
            if isinstance(c, dict):
                count(c)
    count(model["outliner"][0])
    print("cubes:", len(model["elements"]), "bones:", n_groups[0], "animations:",
          [a["name"] for a in model["animations"]])


if __name__ == "__main__":
    main()
