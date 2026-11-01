#!/usr/bin/env python3
"""workshop_engineer — Atelier de l'ingénieur / Engineer's Workshop (reference: scratchpad/ref/workshop_engineer_ref.png).

A wide thick plank roof on four posts with knee brackets, a plank back wall with a big wooden gear wheel, a pinned
blueprint and hanging tools, a long workbench covered with brass gears and mechanisms (a geared box, a vice, a
pressure tank, copper pipes with a valve wheel), a shelf of brass boxes behind it, iron-banded crates stacked at the
left with a metal crate in front, a crate with a brass cylinder at the right, a lantern on a bracket.

Usage:  python3 tools/workshops/generate_workshop_engineer.py    (WS_OUT=<file>: only the model, for previews)
Workshop-local coordinates: y up, +z = front, the anchor block (0, 0, 0) is inside the workbench.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wslib_a as wl  # noqa: E402

NAME = "workshop_engineer"
UP, v3 = wl.UP, wl.v3
XP = 2.35
ZF, ZB = 0.62, -1.3
TOP = 2.75
WALL_Z = -1.36


def frame(root, detail):
    b = wl.Bone("frame", parent=root)
    for s in (1, -1):
        for k, z in enumerate((ZF, ZB)):
            wl.post(b, "post_%d_%d" % (s, k), (s * XP, 0.0, z), (s * XP, TOP, z), d=0.3, region="wood")
            wl.box(detail, "post_band_%d_%d" % (s, k), (s * XP - 0.165, 0.3, z - 0.165), (s * XP + 0.165, 0.38, z + 0.165), "iron")
        wl.beam(b, "side_beam_%d" % s, (s * XP, TOP - 0.12, ZB - 0.35), (s * XP, TOP - 0.12, ZF + 0.45), 0.24, {"all": "wood_dark", "+1": "end_grain", "-1": "end_grain"})
        # the big curved brackets of the picture: two braces each side, front and side
        wl.bracket(b, "brace_f_%d" % s, (s * XP, TOP - 0.85, ZF), (s * (XP - 0.75), TOP - 0.1, ZF), d=0.16)
        wl.bracket(b, "brace_s_%d" % s, (s * XP, TOP - 0.75, ZF), (s * XP, TOP - 0.14, ZF + 0.42), d=0.14)
        wl.bracket(detail, "brace_o_%d" % s, (s * XP, TOP - 0.7, ZF), (s * (XP + 0.42), TOP - 0.06, ZF), d=0.14)
    for e, z in (("f", ZF), ("b", ZB)):
        wl.beam(b, "beam_" + e, (-XP - 0.55, TOP + 0.02, z), (XP + 0.55, TOP + 0.02, z), 0.28, {"all": "wood_dark", "+1": "end_grain", "-1": "end_grain"},
                width=0.26)
    for k in range(18):
        x = -XP + (k + 0.5) * (2 * XP / 18)
        wl.beam(b, "wall_%d" % k, (x, 0.0, WALL_Z), (x, TOP - 0.1, WALL_Z), 0.07, "plank_dark", width=2 * XP / 18 * 0.99, up=v3(0, 0, 1))
    for k, y in enumerate((0.9, 2.45)):
        wl.beam(b, "wall_rail_%d" % k, (-XP, y, WALL_Z + 0.07), (XP, y, WALL_Z + 0.07), 0.12, "wood_dark", width=0.08, up=UP)
    wl.collide((-XP, 0.0, WALL_Z - 0.05, XP, TOP, WALL_Z + 0.05))
    # rafters sticking out at the front and the wide, thick roof
    for k, x in enumerate((-2.55, -1.7, -0.85, 0.0, 0.85, 1.7, 2.55)):
        wl.beam(b, "rafter_%d" % k, (x, TOP + 0.26, ZB - 0.55), (x, TOP + 0.12, ZF + 0.85), 0.18, {"all": "wood", "+1": "end_grain", "-1": "end_grain"})
    wl.plank_roof(b, "roof", -XP - 0.55, XP + 0.55, ZB - 0.5, ZF + 0.72, TOP + 0.62, TOP + 0.46, th=0.22, plank_w=0.34, fascia="wood_dark")
    return b


def wall(root, detail):
    w = wl.Bone("wall", parent=root)
    z = WALL_Z + 0.12
    wl.gear_wheel(w, "big_gear", (-0.95, 1.85, z), 0.62, normal=(0, 0, 1), teeth=14, spokes=6, th=0.12, detail=detail)
    # the pinned blueprint
    wl.plate(w, "blueprint", (0.55, 1.88, WALL_Z + 0.05), (0, 0, 1), UP, 0.82, 0.86, "blueprint", th=0.015)
    for k, (dx, dy) in enumerate(((-0.36, 0.38), (0.36, 0.38))):
        wl.box(detail, "pin_%d" % k, (0.55 + dx - 0.025, 1.88 + dy - 0.025, WALL_Z + 0.05), (0.55 + dx + 0.025, 1.88 + dy + 0.025, WALL_Z + 0.09), "iron")
    # hanging tools: a wrench, dividers, a hammer, a saw, a coil of rope
    wl.box(detail, "tool_rail", (-0.3, 2.28, WALL_Z + 0.04), (0.05, 2.33, WALL_Z + 0.12), "wood_dark")
    wl.beam(detail, "wrench", (-0.2, 2.25, WALL_Z + 0.09), (-0.2, 1.75, WALL_Z + 0.09), 0.035, "steel", width=0.03)
    wl.beam(detail, "wrench_jaw", (-0.26, 1.73, WALL_Z + 0.09), (-0.14, 1.73, WALL_Z + 0.09), 0.06, "steel", width=0.03)
    wl.beam(detail, "dividers_a", (-0.02, 2.25, WALL_Z + 0.09), (-0.08, 1.85, WALL_Z + 0.09), 0.025, "brass")
    wl.beam(detail, "dividers_b", (-0.02, 2.25, WALL_Z + 0.09), (0.04, 1.85, WALL_Z + 0.09), 0.025, "brass")
    wl.box(detail, "tool_rail_r", (1.15, 2.28, WALL_Z + 0.04), (1.75, 2.33, WALL_Z + 0.12), "wood_dark")
    wl.hammer(detail, "wall_hammer", (1.25, 1.85, WALL_Z + 0.1), (0, 1, 0), length=0.4, lying=False)
    wl.beam(detail, "saw_blade", (1.45, 2.2, WALL_Z + 0.08), (1.6, 1.65, WALL_Z + 0.08), 0.01, "steel", width=0.12, up=v3(0, 0, 1))
    wl.beam(detail, "saw_grip", (1.42, 2.27, WALL_Z + 0.08), (1.47, 2.15, WALL_Z + 0.08), 0.05, "wood")
    wl.octo(detail, "rope_coil", (1.75, 1.95, WALL_Z + 0.06), (1.75, 1.95, WALL_Z + 0.16), 0.16, "rope")
    # the shelf of brass boxes behind the bench
    wl.box(w, "shelf_board", (-1.55, 1.28, WALL_Z + 0.02), (1.95, 1.33, WALL_Z + 0.36), {"all": "plank", "+1": "end_grain", "-1": "end_grain"},
           u_dir=v3(1, 0, 0))
    for k, x in enumerate((-1.3, 0.2, 1.7)):
        wl.beam(detail, "shelf_bracket_%d" % k, (x, 1.0, WALL_Z + 0.04), (x, 1.27, WALL_Z + 0.32), 0.05, "wood_dark")
    for k, (x, s) in enumerate(((-1.25, 0.26), (-0.4, 0.3), (0.05, 0.22), (1.0, 0.28))):
        wl.rbox(w, "brass_box_%d" % k, (x, 1.33, WALL_Z + 0.2), (s, s * 0.85, s * 0.8), 0.05 * k, {"all": "brass_box"}, stretch=True)
    wl.small_gear(detail, "shelf_gear_0", (-0.75, 1.33 + 0.13, WALL_Z + 0.22), 0.13, normal=(0, 0, 1))
    wl.small_gear(detail, "shelf_gear_1", (1.45, 1.33 + 0.1, WALL_Z + 0.22), 0.1, normal=(0, 0, 1), region="gear_iron")
    return w


def bench(root, detail):
    b = wl.Bone("bench", parent=root)
    x0, x1, z0, z1 = -1.55, 1.85, -0.5, 0.5
    wl.table(b, "bench", x0, x1, z0, z1, 1.0, top="plank", leg="wood", top_th=0.13, leg_d=0.2, shelf=True)
    # iron bands round the legs, a drawer box under the top
    for i, (x, z) in enumerate(((x0 + 0.14, z0 + 0.14), (x1 - 0.14, z0 + 0.14), (x0 + 0.14, z1 - 0.14), (x1 - 0.14, z1 - 0.14))):
        wl.box(detail, "leg_band_%d" % i, (x - 0.115, 0.55, z - 0.115), (x + 0.115, 0.61, z + 0.115), "iron")
    wl.crate(b, "under_box_0", (-0.9, 0.3, -0.05), size=(0.5, 0.36, 0.5), region="metal_crate", top="metal_crate", solid=False)
    wl.crate(b, "under_box_1", (1.1, 0.3, 0.0), size=(0.42, 0.3, 0.42), solid=False)
    y = 1.0
    # gears and mechanisms on the top
    for k, (x, z, r, reg) in enumerate(((-1.25, 0.25, 0.12, "gear"), (-1.0, 0.05, 0.09, "gear_iron"), (-0.15, 0.3, 0.1, "gear"),
                                        (0.25, 0.2, 0.07, "gear"), (0.55, 0.32, 0.09, "gear_iron"))):
        wl.small_gear(detail, "bench_gear_%d" % k, (x, y + 0.02 + 0.03 * (k % 2), z), r, normal=(0, 1, 0))
    # the geared box (a mechanism with a gear face standing on it)
    wl.rbox(b, "mech_box", (-0.65, y, -0.25), (0.36, 0.3, 0.3), 0.1, {"all": "brass_box"}, stretch=True)
    wl.small_gear(b, "mech_gear", (-0.65, y + 0.2, -0.08), 0.15, normal=(0, 0, 1))
    wl.small_gear(detail, "mech_gear2", (-0.47, y + 0.38, -0.25), 0.11, normal=(1, 0, 0), region="gear_iron")
    wl.octo(detail, "mech_axle", (-0.65, y + 0.2, -0.3), (-0.65, y + 0.2, -0.04), 0.025, "steel")
    # a small brass clockwork with a crank
    wl.rbox(b, "clock_box", (0.0, y, -0.25), (0.26, 0.22, 0.24), -0.15, {"all": "brass_box"}, stretch=True)
    wl.small_gear(detail, "clock_gear", (0.0, y + 0.25, -0.25), 0.1, normal=(0, 1, 0))
    wl.beam(detail, "clock_crank", (0.14, y + 0.15, -0.2), (0.24, y + 0.15, -0.12), 0.025, "iron")
    # a vice at the right front of the bench
    vx = 1.05
    wl.rbox(b, "vice_base", (vx, y, 0.32), (0.22, 0.08, 0.18), 0.0, "iron")
    wl.rbox(b, "vice_jaw_a", (vx - 0.06, y + 0.08, 0.32), (0.08, 0.16, 0.16), 0.0, "iron")
    wl.rbox(b, "vice_jaw_b", (vx + 0.07, y + 0.08, 0.32), (0.08, 0.16, 0.16), 0.0, "iron")
    wl.octo(detail, "vice_screw", (vx + 0.1, y + 0.16, 0.32), (vx + 0.32, y + 0.16, 0.32), 0.02, "steel")
    wl.octo(detail, "vice_handle", (vx + 0.32, y + 0.08, 0.32), (vx + 0.32, y + 0.25, 0.32), 0.015, "steel")
    # the pressure tank with copper pipes and a valve wheel at the right end
    tx = 1.5
    wl.octo(b, "tank", (tx, y, -0.2), (tx, y + 0.42, -0.2), 0.14, "steel", end="iron")
    wl.octo(b, "tank_dome", (tx, y + 0.42, -0.2), (tx, y + 0.5, -0.2), 0.1, "iron")
    for k, yy in enumerate((y + 0.08, y + 0.34)):
        wl.octo(detail, "tank_band_%d" % k, (tx, yy, -0.2), (tx, yy + 0.04, -0.2), 0.15, "brass")
    wl.pipe(detail, "pipe_a", [(tx, y + 0.5, -0.2), (tx, y + 0.65, -0.2), (tx - 0.35, y + 0.65, -0.2), (tx - 0.35, y + 0.2, -0.2)])
    wl.pipe(detail, "pipe_b", [(tx + 0.12, y + 0.25, -0.2), (tx + 0.28, y + 0.25, -0.2), (tx + 0.28, y + 0.8, -0.2), (tx + 0.28, y + 0.8, -0.55)])
    wl.octo(detail, "valve_stem", (tx - 0.35, y + 0.42, -0.2), (tx - 0.35, y + 0.42, -0.08), 0.015, "steel")
    wl.small_gear(detail, "valve_wheel", (tx - 0.35, y + 0.42, -0.07), 0.07, normal=(0, 0, 1), region="gear_iron")
    wl.octo(b, "gauge", (tx, y + 0.3, -0.06), (tx, y + 0.3, -0.04), 0.05, "brass", end="white")
    # tools lying on the bench: a wrench, screwdriver, a hammer, a lens on a stand, a roll of plans
    wl.beam(detail, "bench_wrench", (0.3, y + 0.015, 0.05), (0.62, y + 0.015, -0.05), 0.025, "steel", width=0.035, up=UP)
    wl.hammer(detail, "bench_hammer", (-1.45, y + 0.04, -0.1), (1, 0, -0.5), length=0.32)
    wl.beam(detail, "screwdriver", (0.75, y + 0.02, 0.15), (0.95, y + 0.02, 0.05), 0.02, "steel")
    wl.beam(detail, "screwdriver_grip", (0.67, y + 0.025, 0.19), (0.75, y + 0.025, 0.15), 0.04, "wood")
    wl.beam(detail, "lens_arm", (0.45, y, -0.3), (0.45, y + 0.3, -0.2), 0.02, "brass")
    wl.small_gear(detail, "lens", (0.45, y + 0.32, -0.15), 0.06, normal=(0, 0.3, 1), region="gear")
    wl.octo(b, "plans_roll", (-0.3, y + 0.05, 0.3), (0.15, y + 0.05, 0.32), 0.05, "parchment", end="parchment")
    wl.rbox(detail, "plans_sheet", (-0.55, y, 0.15), (0.4, 0.01, 0.3), 0.25, "blueprint", stretch=True)
    return b


def crates(root, detail):
    c = wl.Bone("crates", parent=root)
    # the stack at the left, the metal crate in front of the bench's left end
    wl.crate(c, "left_low", (-1.98, 0.0, 0.05), size=(0.85, 0.9, 0.85), solid=True)
    wl.crate(c, "left_high", (-1.98, 0.9, 0.02), size=(0.76, 0.7, 0.76), yaw=0.04, solid=True)
    wl.crate(c, "left_back", (-2.0, 0.0, -0.85), size=(0.7, 0.75, 0.7), yaw=-0.05, solid=True)
    wl.crate(c, "metal", (-1.25, 0.0, 0.97), size=(0.85, 0.75, 0.66), region="metal_crate", top="metal_crate", yaw=0.03, solid=True)
    wl.box(detail, "metal_latch", (-1.33, 0.32, 1.29), (-1.17, 0.52, 1.32), "iron")
    for s in (1, -1):
        wl.box(detail, "metal_handle_%d" % s, (-1.25 + s * 0.43 - 0.02, 0.48, 0.82), (-1.25 + s * 0.43 + 0.02, 0.53, 1.1), "iron")
    # loose parts on the stack: a gear leaning, a coil of copper wire, a small brass box
    wl.small_gear(detail, "stack_gear", (-2.1, 1.6 + 0.16, 0.25), 0.16, normal=(0.2, 0, 1))
    wl.octo(detail, "wire_coil", (-1.8, 1.6, -0.15), (-1.8, 1.68, -0.15), 0.12, "copper")
    wl.rbox(detail, "stack_box", (-1.85, 1.6, 0.2), (0.2, 0.16, 0.18), 0.3, {"all": "brass_box"}, stretch=True)
    # the crate at the right with a brass cylinder and a small boiler on it
    wl.crate(c, "right", (2.0, 0.0, -0.1), size=(0.66, 0.85, 0.8), solid=True)
    wl.octo(c, "cylinder", (2.0, 0.85, -0.25), (2.0, 1.3, -0.25), 0.16, "brass", end="iron")
    wl.octo(detail, "cylinder_cap", (2.0, 1.3, -0.25), (2.0, 1.4, -0.25), 0.1, "iron")
    wl.octo(detail, "cylinder_spout", (2.0, 1.35, -0.25), (2.0, 1.35, 0.0), 0.03, "copper")
    wl.chest(c, "right_chest", (2.0, 0.85, 0.15), size=(0.5, 0.22, 0.32), solid=False, detail=detail)
    # a lantern on an iron bracket from the left front post
    wl.hanging_lantern(c, "lantern", (-XP + 0.6, 2.2, ZF - 0.05), drop=0.12, size=0.34, arm=(-XP + 0.15, 2.2, ZF))
    return c


def extras(root, detail):
    """A second wooden gear meshing with the big one, small gears on the wall, an oil barrel, an oil can, a
    bucket of bolts, pliers."""
    e = wl.Bone("extras", parent=root)
    wl.gear_wheel(e, "gear_small", (-1.78, 2.45, WALL_Z + 0.12), 0.34, normal=(0, 0, 1), teeth=9, spokes=4, th=0.1, detail=detail)
    for k, (x, y, r, reg) in enumerate(((0.05, 1.62, 0.1, "gear"), (1.95, 1.65, 0.13, "gear_iron"), (2.1, 2.2, 0.09, "gear"))):
        wl.small_gear(detail, "wall_gear_%d" % k, (x, y, WALL_Z + 0.06), r, normal=(0, 0, 1), region=reg)
    wl.barrel(e, "oil_barrel", (1.95, 0.0, -0.88), r=0.3, h=0.82)
    wl.octo(detail, "oil_can", (1.15, 1.0, -0.3), (1.15, 1.14, -0.3), 0.06, "copper", end="iron")
    wl.beam(detail, "oil_spout", (1.15, 1.12, -0.26), (1.15, 1.22, -0.12), 0.02, "copper")
    wl.tub(e, "bolt_bucket", (0.3, 0.3, 0.05), r=0.14, h=0.2, staves=8, handles=False, solid=False)
    wl.rbox(detail, "bolts", (0.3, 0.47, 0.05), (0.2, 0.03, 0.2), 0.4, "iron", stretch=True)
    for k, d in enumerate((v3(1, 0, 0.25), v3(1, 0, -0.25))):
        wl.beam(detail, "pliers_%d" % k, v3(-0.1, 1.015, 0.38), v3(-0.1, 1.015, 0.38) + wl.norm(d) * 0.2, 0.02, "steel", up=UP)
    for k in range(3):
        wl.rbox(detail, "plate_stack_%d" % k, (1.42, 0.3 + 0.03 * k, 0.1), (0.36, 0.03, 0.28), 0.06 * k, "steel", stretch=True)
    return e


def build():
    root = wl.Bone(NAME)
    detail = wl.Bone("detail", parent=root)
    frame(root, detail)
    wall(root, detail)
    bench(root, detail)
    crates(root, detail)
    extras(root, detail)
    return root


def icon(path):
    """A gear (the reference sheet's pictogram)."""
    im = wl.icon_canvas()
    p = im.load()
    cx, cy = 7.5, 7.5
    for y in range(16):
        for x in range(16):
            dx, dy = x - cx, y - cy
            r = math.hypot(dx, dy)
            a = math.atan2(dy, dx)
            outer = 7.4 if math.cos(a * 8) > 0.2 else 5.6
            if r <= outer and r > 2.0:
                shade = 1.0 + 0.25 * (-dx - dy) / 10
                base = (196, 148, 56) if r < 5.4 else (170, 120, 44)
                p[x, y] = tuple(int(min(255, c * shade)) for c in base) + (255,)
            elif r <= 2.0 and r > 1.0:
                p[x, y] = (110, 76, 26, 255)
    im.save(path)


def main():
    wl.setup(NAME)
    root = build()
    wl.export(root, NAME, None, icon=icon, particles=[wl.particle("smoke", (1.78, 1.85, -0.55), 0.06, 1)], visible_box=(8, 5, 0))


if __name__ == "__main__":
    main()
