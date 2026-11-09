"""Furniture made for the Gear Steamship (what the decoration mods lack), drawn by tools/generate_gear_steam.py
from the CUSTOM list of tools/gear_steam_decor.py:

  the engine room's twin-cylinder steam engine (its flywheel and crankshaft turn with the ship's engine, bone
  gear_flywheel; its two pistons rise and fall, bones piston_0 / piston_1), the coal bunker with its shovel,
  the steam pipes along the ceiling with their valves, the gauge boards, the railing round the stair hatch, the
  engine-order telegraph (the bridge and its repeater in the engine room), the copper cowl ventilators on the
  engine house roof, the steam windlass and the mooring bitts on the forecastle, chain coils, the windows seen from
  inside, the galley stove's stovepipe, a spare gear wheel and a stack of copper pipes in the hold.

Pipes, valves, gauges, barrels, chests, the navigator's instruments, shelves, rugs and the like come from
tools/leviathan_furniture.py (read only): their "in_*" regions are in this ship's atlas (tools/gear_steam_texture.py).

Every builder takes the bone, a name and its placement (ship-local blocks: +x port, +y up, +z bow). Cubes inside
the hull are named "lit_*" (lit by the ship's lamps in the rooms), "glow_*" are full bright.
"""
import math

import numpy as np

import generate_galley as gg
import generate_airship as ga
import leviathan_furniture as lf
import corsair_furniture as cf

v3, norm, add_cube, beam, Bone = gg.v3, gg.norm, gg.add_cube, gg.beam, gg.Bone
EYE = np.eye(3)
prism, disc, ring, tube = ga.prism, ga.disc, ga.ring, ga.tube

FLYWHEEL_TURNS = 2        # whole turns of the flywheel per loop of the "engine" animation (4 units of distance)
PISTON_STROKE = 0.25      # crank throw (blocks): each piston moves +- this much


def _box(bone, name, c, size, region, R=EYE, **kw):
    return add_cube(bone, name, v3(*c), R, size, region, **kw)


# ---------------------------------------------------------------- the engine room
def steam_engine(bone, name, x, z, y, side=1):
    """An inverted vertical twin-cylinder engine on the port side of the engine room: a riveted bed plate, two
    pedestal bearings carrying the crankshaft across the ship (axis x) with the flywheel at its inboard end (the
    wheel's face towards the aisle), A-frame columns carrying an entablature and the two riveted cylinders with
    their brass bands and covers, piston rods and crossheads sliding in their guides (bones piston_k), the
    steam chest between the cylinders. x: plane of the flywheel, z: the shaft's position along the ship, y: floor."""
    s = side
    y_shaft = y + 1.45
    xs = [x + s * 0.9, x + s * 1.7]          # the two cylinders along the shaft
    x_end = x + s * 2.2
    # bed plate and bearings
    _box(bone, "lit_%s_bed" % name, ((x + x_end) / 2 + s * 0.15, y + 0.15, z), (abs(x_end - x) + 0.1, 0.3, 1.5),
         {"all": "iron_band", "+2": "in_rivets"})
    for k, xb in enumerate((x + s * 0.35, x_end - s * 0.05)):
        _box(bone, "lit_%s_pedestal_%d" % (name, k), (xb, y + 0.3 + (y_shaft - y - 0.3) / 2, z), (0.36, y_shaft - y - 0.3 - 0.1, 0.62), "iron_dark")
        _box(bone, "lit_%s_cap_%d" % (name, k), (xb, y_shaft + 0.05, z), (0.42, 0.24, 0.5), "brass")
    # A-frames: four columns from the bed to the entablature, braced
    top = y + 2.3
    for k, xc in enumerate(xs):
        for e in (-1, 1):
            a = v3(xc, y + 0.3, z + e * 0.62)
            b = v3(xc, top, z + e * 0.42)
            beam(bone, "lit_%s_column_%d%d" % (name, k, e > 0), a, b, 0.14, "iron_dark", width=0.16)
    beam(bone, "lit_%s_brace" % name, v3(xs[0], y + 0.6, z - 0.6), v3(xs[1], top - 0.15, z - 0.42), 0.08, "iron")
    _box(bone, "lit_%s_entablature" % name, ((xs[0] + xs[1]) / 2, top + 0.05, z), (abs(xs[1] - xs[0]) + 0.9, 0.12, 1.05),
         {"all": "iron_band", "+2": "in_rivets"})
    # the cylinders, their covers, bands and drain cocks; the steam chest between them
    c0, c1 = top + 0.11, top + 1.35
    for k, xc in enumerate(xs):
        prism(bone, "lit_%s_cyl_%d" % (name, k), v3(xc, (c0 + c1) / 2, z), v3(0, 1, 0), v3(1, 0, 0), c1 - c0, 0.4, 12, "boiler")
        for j, yy in enumerate((c0 + 0.08, c1 - 0.06)):
            prism(bone, "lit_%s_cyl_band_%d%d" % (name, k, j), v3(xc, yy, z), v3(0, 1, 0), v3(1, 0, 0), 0.1, 0.43, 12, "brass")
        disc(bone, "lit_%s_cyl_cover_%d" % (name, k), v3(xc, c1 + 0.03, z), (0, 1, 0), 0.34, 0.06, "brass", sides=12)
        disc(bone, "lit_%s_cyl_boss_%d" % (name, k), v3(xc, c1 + 0.09, z), (0, 1, 0), 0.12, 0.06, "iron", sides=8)
        tube(bone, "lit_%s_cock_%d" % (name, k), v3(xc, c0 + 0.2, z + 0.4), v3(xc, c0 + 0.2, z + 0.58), 0.06, "brass", sides=4)
    xm = (xs[0] + xs[1]) / 2
    _box(bone, "lit_%s_chest" % name, (xm, (c0 + c1) / 2 + 0.1, z - 0.32), (0.42, c1 - c0 - 0.3, 0.42), {"all": "boiler", "+2": "brass"})
    # guides on each side of the rods (static), the rods and crossheads (moving)
    for k, xc in enumerate(xs):
        for e in (-1, 1):
            _box(bone, "lit_%s_guide_%d%d" % (name, k, e > 0), (xc, (y_shaft - 0.05 + top) / 2, z + e * 0.2), (0.06, top - y_shaft + 0.05, 0.05),
                 "steel")
        pb = Bone("piston_%d" % k, origin=(xc, y_shaft + 0.55, z), parent=bone)
        tube(pb, "lit_%s_rod_%d" % (name, k), v3(xc, y_shaft + 0.55, z), v3(xc, top + 0.75, z), 0.09, "steel", sides=4)
        _box(pb, "lit_%s_crosshead_%d" % (name, k), (xc, y_shaft + 0.55, z), (0.24, 0.16, 0.3), "brass")
        beam(pb, "lit_%s_conrod_%d" % (name, k), v3(xc, y_shaft + 0.5, z), v3(xc, y_shaft + 0.18, z), 0.1, "iron", width=0.12)
    # the crankshaft, its cranks and the flywheel: one bone turning about the shaft (axis x)
    fb = Bone("gear_flywheel", origin=(x, y_shaft, z), parent=bone)
    tube(fb, "lit_%s_shaft" % name, v3(x - s * 0.2, y_shaft, z), v3(x_end + s * 0.1, y_shaft, z), 0.18, "steel", sides=8)
    for k, xc in enumerate(xs):
        ph = 1 if k == 0 else -1   # the cranks half a turn apart
        for e in (-1, 1):
            _box(fb, "lit_%s_web_%d%d" % (name, k, e > 0), (xc + e * 0.12, y_shaft + ph * PISTON_STROKE / 2, z),
                 (0.06, PISTON_STROKE + 0.22, 0.2), "iron")
        tube(fb, "lit_%s_pin_%d" % (name, k), v3(xc - 0.15, y_shaft + ph * PISTON_STROKE, z), v3(xc + 0.15, y_shaft + ph * PISTON_STROKE, z), 0.1,
             "brass", sides=6)
    r = 1.15
    ring(fb, "lit_%s_fly_rim" % name, v3(x, y_shaft, z), (1, 0, 0), r - 0.1, 0.2, "iron_dark", n=16)
    ring(fb, "lit_%s_fly_tyre" % name, v3(x + s * 0.03, y_shaft, z), (1, 0, 0), r - 0.02, 0.06, "brass", n=16)
    for k in range(6):
        a = 2 * math.pi * k / 6
        d = v3(0, math.cos(a), math.sin(a))
        beam(fb, "lit_%s_fly_spoke_%d" % (name, k), v3(x, y_shaft, z) + d * 0.18, v3(x, y_shaft, z) + d * (r - 0.18), 0.12, "iron_dark",
             width=0.16, up=v3(1, 0, 0))
    disc(fb, "lit_%s_fly_hub" % name, v3(x, y_shaft, z), (1, 0, 0), 0.24, 0.3, "brass", sides=8)


def coal_bunker(bone, name, x0, x1, z0, z1, y, h=1.0):
    """An open bunker of riveted iron plates, heaped with coal, a shovel stuck in the heap."""
    t = 0.08
    xc, zc = (x0 + x1) / 2, (z0 + z1) / 2
    w, d = x1 - x0, z1 - z0
    for k, (c, size) in enumerate((((xc, z0 + t / 2), (w, t)), ((xc, z1 - t / 2), (w, t)), ((x0 + t / 2, zc), (t, d)),
                                   ((x1 - t / 2, zc), (t, d)))):
        sx, sz = size
        _box(bone, "lit_%s_wall_%d" % (name, k), (c[0], y + h / 2, c[1]), (sx, h, sz), {"all": "in_rivets"})
        _box(bone, "lit_%s_rim_%d" % (name, k), (c[0], y + h + 0.03, c[1]), (sx + 0.04, 0.06, sz + 0.04), "brass")
    _box(bone, "lit_%s_fill" % name, (xc, y + h * 0.4, zc), (w - 2 * t - 0.02, h * 0.8, d - 2 * t - 0.02), {"all": None, "+2": "coal"})
    for k, (dx, dz, s) in enumerate(((0.0, 0.0, 1.0), (0.25, -0.15, 0.7), (-0.3, 0.2, 0.6))):
        lf.coal_heap(bone, "%s_heap_%d" % (name, k), (xc + dx * w, y + h * 0.8, zc + dz * d), r=min(w, d) * 0.45 * s)
    # the shovel: blade in the coal, the shaft leaning out
    a = v3(xc + w * 0.2, y + h * 0.9, zc + d * 0.15)
    b = a + v3(0.25 * np.sign(-xc), 1.0, 0.25)
    beam(bone, "lit_%s_shovel_shaft" % name, a, b, 0.05, "wood_mid")
    _box(bone, "lit_%s_shovel_blade" % name, a - v3(0, 0.1, 0), (0.24, 0.2, 0.04), "iron", R=gg.ry(0.4))


def pipe(bone, name, pts, d=0.28, region="pipe", flange="brass"):
    """A copper pipe along a polyline with a brass flange at every joint."""
    lf.pipe(bone, name, pts, d=d, region=region, flange=flange, sides=8)


def valve(bone, name, p, normal, r=0.2):
    lf.valve(bone, name, p, normal, r=r, region="red_paint")


def gauge_board(bone, name, center, normal, w=1.2, h=0.8):
    lf.gauge_board(bone, name, center, normal, w=w, h=h)


def hatch_rail(bone, name, pts, h=1.0):
    """An iron railing round a hatch (base points on the floor)."""
    lf.railing(bone, name, pts, h=h, step=0.7, region="iron_dark")


def telegraph(bone, name, p, facing=(0, 0, -1), lit=True):
    """An engine-order telegraph: a brass pedestal, a round head with a dial on each face and a handle."""
    pre = "lit_" if lit else ""
    p = v3(*p)
    n = norm(v3(facing[0], 0, facing[2]))
    u = np.cross(v3(0, 1, 0), n)
    R = np.column_stack([u, v3(0, 1, 0), n])
    disc(bone, pre + "%s_foot" % name, p + v3(0, 0.04, 0), (0, 1, 0), 0.22, 0.08, "brass", sides=8)
    tube(bone, pre + "%s_column" % name, p + v3(0, 0.06, 0), p + v3(0, 0.9, 0), 0.16, "brass", sides=8)
    hc = p + v3(0, 1.08, 0)
    disc(bone, pre + "%s_head" % name, hc, n, 0.24, 0.16, "brass", sides=12)
    for e in (-1, 1):
        add_cube(bone, pre + "%s_dial_%d" % (name, e > 0), hc + n * (e * 0.09), R, (0.4, 0.4, 0.012), {"all": None, "+3": "gauge", "-3": "gauge"},
                 stretch=True)
    beam(bone, pre + "%s_handle" % name, hc + n * 0.12, hc + n * 0.14 + v3(0, 0.3, 0) + u * 0.12, 0.04, "iron")
    _box(bone, pre + "%s_knob" % name, hc + n * 0.14 + v3(0, 0.32, 0) + u * 0.13, (0.08, 0.08, 0.08), "red_paint")


def speaking_tube(bone, name, p, top, lit=True):
    """A brass voice pipe rising from the floor to a bell mouth."""
    pre = "lit_" if lit else ""
    p = v3(*p)
    tube(bone, pre + "%s_pipe" % name, p, p + v3(0, top, 0), 0.1, "brass", sides=6)
    tube(bone, pre + "%s_mouth" % name, p + v3(0, top - 0.04, 0), p + v3(0, top + 0.1, 0), 0.22, "brass", sides=8)


# ---------------------------------------------------------------- the decks
def ventilator(bone, name, p, facing=(0, 0, 1), h=1.2, r=0.22):
    """A copper cowl ventilator: a riveted pipe on a brass collar, its bell mouth turned to `facing`."""
    p = v3(*p)
    n = norm(v3(facing[0], 0, facing[2]))
    disc(bone, "%s_collar" % name, p + v3(0, 0.06, 0), (0, 1, 0), r + 0.08, 0.12, "brass", sides=10)
    tube(bone, "%s_pipe" % name, p + v3(0, 0.1, 0), p + v3(0, h, 0), 2 * r, "copper2", sides=10)
    elbow = p + v3(0, h, 0)
    tube(bone, "%s_bend" % name, elbow - v3(0, 0.05, 0), elbow + v3(0, 0.12, 0) + n * 0.12, 2 * r + 0.02, "copper2", sides=10)
    mouth = elbow + v3(0, 0.2, 0) + n * 0.28
    tube(bone, "%s_bell" % name, mouth - n * 0.18, mouth + n * 0.06, 2 * r + 0.24, "copper2", sides=12)
    tube(bone, "%s_bell_rim" % name, mouth + n * 0.04, mouth + n * 0.1, 2 * r + 0.3, "brass", sides=12)
    disc(bone, "%s_throat" % name, mouth - n * 0.1, n, r + 0.08, 0.02, "iron_dark", sides=10)


def windlass(bone, name, p, width=1.7):
    """A steam anchor windlass across the forecastle: two iron cheeks, the barrel with its chain gypsies, a brass
    gear wheel at one end, a small steam cylinder, the chains running forward to the hawse pipes."""
    p = v3(*p)
    hw = width / 2
    for e in (-1, 1):
        _box(bone, "%s_cheek_%d" % (name, e > 0), p + v3(e * hw, 0.45, 0), (0.14, 0.9, 0.8), {"all": "iron_dark", "+2": "iron"})
    _box(bone, "%s_bed" % name, p + v3(0, 0.08, 0), (width + 0.2, 0.16, 0.9), "iron_band")
    yb = 0.55
    tube(bone, "%s_barrel" % name, p + v3(-hw, yb, 0), p + v3(hw, yb, 0), 0.34, "iron", sides=10)
    for e in (-1, 1):
        disc(bone, "%s_gypsy_%d" % (name, e > 0), p + v3(e * hw * 0.5, yb, 0), (1, 0, 0), 0.3, 0.2, "iron_dark", sides=10)
        disc(bone, "%s_brake_%d" % (name, e > 0), p + v3(e * hw * 0.8, yb, 0), (1, 0, 0), 0.24, 0.08, "brass", sides=10)
        # the chain from the gypsy forward and down to the hawse pipe
        a = p + v3(e * hw * 0.5, yb + 0.25, 0.1)
        b = p + v3(e * hw * 0.5, 0.05, 1.05)
        n = int(max(2, np.linalg.norm(b - a) / 0.16))
        for k in range(n):
            q = a + (b - a) * (k + 0.5) / n
            rot = gg.ry(0) if k % 2 == 0 else gg.rz(math.pi / 2)
            add_cube(bone, "%s_chain_%d_%d" % (name, e > 0, k), q, rot, (0.06, 0.12, 0.16), "chain")
        disc(bone, "%s_hawse_%d" % (name, e > 0), b + v3(0, -0.02, 0.05), (0, 1, 0), 0.16, 0.06, "brass", sides=8)
    lf.gear(bone, "%s_gear" % name, p + v3(hw + 0.12, yb + 0.05, 0), (1, 0, 0), 0.38, 0.08, teeth=12, region="brass", spokes=4, rim="brass",
            hub="iron")
    prism(bone, "%s_cylinder" % name, p + v3(-hw + 0.3, 0.75, -0.42), v3(0, 0, 1), v3(1, 0, 0), 0.45, 0.16, 8, "boiler")
    pipe(bone, "%s_steam" % name, [p + v3(-hw + 0.3, 0.75, -0.65), p + v3(-hw + 0.3, 0.2, -0.65)], d=0.1)


def bitts(bone, name, p, along=(1, 0, 0)):
    """Mooring bitts: two iron posts with caps on a base plate, joined by a crossbar."""
    p = v3(*p)
    a = norm(v3(*along))
    R = np.column_stack([a, v3(0, 1, 0), np.cross(a, v3(0, 1, 0))])
    _box(bone, "%s_base" % name, p + v3(0, 0.04, 0), (0.95, 0.08, 0.4), "iron_band", R=R)
    for e in (-1, 1):
        q = p + a * (e * 0.28)
        prism(bone, "%s_post_%d" % (name, e > 0), q + v3(0, 0.33, 0), v3(0, 1, 0), v3(1, 0, 0), 0.5, 0.13, 8, "iron_dark")
        disc(bone, "%s_cap_%d" % (name, e > 0), q + v3(0, 0.6, 0), (0, 1, 0), 0.17, 0.06, "brass", sides=8)
    tube(bone, "%s_bar" % name, p - a * 0.28 + v3(0, 0.42, 0), p + a * 0.28 + v3(0, 0.42, 0), 0.07, "iron", sides=6)


def chain_coil(bone, name, p, r=0.35, turns=3, lit=False):
    """A coil of chain lying on the deck (dark iron links)."""
    pre = "lit_" if lit else ""
    p = v3(*p)
    for k in range(turns):
        rr = r * (1.0 - 0.22 * k)
        n = max(6, int(2 * math.pi * rr / 0.16))
        for j in range(n):
            a = 2 * math.pi * (j + 0.3 * k) / n
            q = p + v3(math.cos(a) * rr, 0.05 + 0.08 * k, math.sin(a) * rr)
            rot = gg.ry(-a) if j % 2 == 0 else gg.ry(-a) @ gg.rx(math.pi / 2)
            add_cube(bone, "%s%s_%d_%d" % (pre, name, k, j), q, rot, (0.06, 0.1, 0.16), "chain")


# ---------------------------------------------------------------- the rooms
def window_in(bone, name, center, normal, w=1.2, h=1.3):
    """A square window seen from inside: the daylight panes, a brass frame and a sill."""
    R, u, n = lf.frame(normal)
    c = v3(*center)
    add_cube(bone, "glow_%s" % name, c + n * 0.02, R, (w, h, 0.012), {"all": None, "+3": "window_in", "-3": "window_in"}, stretch=True,
             u_dir=u, v_dir=v3(0, -1, 0))
    for e in (-1, 1):
        _box(bone, "lit_%s_jamb_%d" % (name, e > 0), c + u * e * (w / 2 + 0.05) + n * 0.04, (0.1, h + 0.2, 0.06), "brass_band", R=R)
        _box(bone, "lit_%s_rail_%d" % (name, e > 0), c + v3(0, e * (h / 2 + 0.05), 0) + n * 0.04, (w + 0.2, 0.1, 0.06), "brass_band", R=R)
    _box(bone, "lit_%s_sill" % name, c - v3(0, h / 2 + 0.12, 0) + n * 0.1, (w + 0.3, 0.06, 0.18), "wood_dark", R=R)


def stovepipe(bone, name, p0, top, d=0.22):
    """The galley stove's iron stovepipe up through the ceiling, banded with brass."""
    p0 = v3(*p0)
    tube(bone, "lit_%s" % name, p0, v3(p0[0], top, p0[2]), d, "iron_dark", sides=8)
    for k, y in enumerate((p0[1] + 0.15, (p0[1] + top) / 2)):
        tube(bone, "lit_%s_band_%d" % (name, k), v3(p0[0], y - 0.03, p0[2]), v3(p0[0], y + 0.03, p0[2]), d + 0.05, "brass", sides=8)
    disc(bone, "lit_%s_collar" % name, v3(p0[0], top - 0.03, p0[2]), (0, 1, 0), d * 0.9, 0.04, "iron", sides=8)


def spare_gear(bone, name, p, normal, r=0.9, lean=0.18):
    """A spare brass gear wheel standing on its edge, leaning against the hull side (p: its foot)."""
    n = norm(v3(*normal))
    c = v3(*p) + v3(0, r, 0) + n * 0.1
    axis = norm(n * math.cos(lean) + v3(0, math.sin(lean), 0))
    lf.gear(bone, "lit_%s" % name, c, axis, r, 0.14, teeth=14, region="brass", spokes=6, rim="brass", hub="iron")


def pipe_stack(bone, name, p, along=(0, 0, 1), length=2.2, n=3, d=0.26):
    """Spare copper pipes lying stacked on two chocks."""
    p = v3(*p)
    a = norm(v3(*along))
    side = np.cross(v3(0, 1, 0), a)
    for e in (-1, 1):
        _box(bone, "lit_%s_chock_%d" % (name, e > 0), p + a * (e * length * 0.32) + v3(0, 0.06, 0), (0.12, 0.12, 0.12), "wood_dark",
             R=np.column_stack([side, v3(0, 1, 0), a]))
        beam(bone, "lit_%s_chockbar_%d" % (name, e > 0), p + a * (e * length * 0.32) + side * (0.45) + v3(0, 0.06, 0),
             p + a * (e * length * 0.32) - side * 0.45 + v3(0, 0.06, 0), 0.12, "wood_dark")
    k = 0
    row, y = n, 0.12 + d / 2
    while row > 0:
        for j in range(row):
            off = (j - (row - 1) / 2) * (d + 0.02)
            q = p + side * off + v3(0, y, 0)
            tube(bone, "lit_%s_%d" % (name, k), q - a * length / 2, q + a * length / 2, d, "pipe", sides=8)
            k += 1
        row -= 1
        y += d * 0.85


def tankards(bone, name, pts):
    cf.tankards(bone, name, pts)


# builder name -> function (CUSTOM entries of tools/gear_steam_decor.py)
BUILDERS = {
    "steam_engine": steam_engine, "coal_bunker": coal_bunker, "pipe": pipe, "valve": valve, "gauge_board": gauge_board,
    "hatch_rail": hatch_rail, "telegraph": telegraph, "speaking_tube": speaking_tube, "ventilator": ventilator, "windlass": windlass,
    "bitts": bitts, "chain_coil": chain_coil, "window_in": window_in, "stovepipe": stovepipe, "spare_gear": spare_gear,
    "pipe_stack": pipe_stack, "tankards": tankards,
    # from tools/leviathan_furniture.py (read only)
    "sea_chest": lf.sea_chest, "upright_barrel": lf.barrel, "cask": lf.cask, "rope_coil": lf.rope_coil, "sack": lf.sack,
    "jar_shelf": lf.jar_shelf, "book_shelf": lf.book_shelf, "wall_map": lf.wall_map, "compass": lf.compass, "sextant": lf.sextant,
    "dividers": lf.dividers, "map_roll": lf.map_roll, "chart_sheet2": lf.chart_sheet, "inkwell": lf.inkwell, "hourglass": lf.hourglass,
    "lever_bank": lf.lever_bank, "pressure_tank": lf.pressure_tank, "wall_bracket": lf.wall_bracket, "rug2": lf.rug,
    "bed_blanket": lf.bed_blanket, "candle": lf.candle, "coal_heap_floor": lf.coal_heap,
}
