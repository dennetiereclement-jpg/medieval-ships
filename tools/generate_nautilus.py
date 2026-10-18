#!/usr/bin/env python3
"""Generates the Nautilus (nautilus) Blockbench model, its texture, its item icon and its interior grid.

Usage:  python3 tools/generate_nautilus.py

Outputs:
  blockbench/nautilus.bbmodel                                            (editable, texture embedded)
  src/main/resources/assets/medievalships/models/entity/nautilus.bbmodel  (loaded by the mod)
  src/main/resources/assets/medievalships/textures/entity/nautilus.png
  src/main/resources/assets/medievalships/textures/item/nautilus.png
  src/main/resources/assets/medievalships/interiors/nautilus.grid         (collisions, dry rooms, ladders, doors)

Step 1 of docs/NAUTILUS_PLAN.md (prototype): the elliptical copper hull in tilted panels, a ram,
the tail with its propeller and fin, the wheelhouse; inside, the walls, floors and ceilings are
drawn exactly on the boundaries of the interior grid (elements named "lit*", lit by the
Nautilus's own lamps), with the ladders and the hatch (bone door_0).

Bones used by the mod (keep their names when editing in Blockbench):
  propeller (propeller: played with the signed speed)    door_<k> (door k: 0 = closed, 1 = open)
"""
import math
import os
import sys
import uuid

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import generate_galleon as gn  # noqa: E402
import generate_galley as gg  # noqa: E402
import nautilus_shape as ns  # noqa: E402
import nautilus_interior as ni  # noqa: E402
import nautilus_texture as nt  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_uuid_counter = [0]


def new_uuid():
    _uuid_counter[0] += 1
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "medievalships/nautilus/%d" % _uuid_counter[0]))


gg.new_uuid = new_uuid
gn.new_uuid = new_uuid
gn.REGIONS = {k: (0,) + r for k, r in nt.REGIONS.items()}
gn.SIZE = nt.SIZE

v3, norm, Bone, add_cube, beam, board = gg.v3, gg.norm, gg.Bone, gg.add_cube, gg.beam, gg.board
rx, ry, rz = gg.rx, gg.ry, gg.rz
EYE = np.eye(3)

NAZ = 32
HULL_S = [-1.0, -0.97, -0.92, -0.85, -0.76, -0.65, -0.52, -0.38, -0.24, -0.1, 0.05, 0.2, 0.35, 0.5, 0.63, 0.74, 0.83,
          0.9, 0.95, 0.985, 1.0]


def hull_z(s):
    return s * ns.BOW_Z if s >= 0 else -s * ns.STERN_Z


def P(z, az_deg, out=0.0):
    a = math.radians(az_deg)
    w, h = ns.half_width(z) + out, ns.half_height(z) + out
    return v3(math.sin(a) * w, ns.AXIS_Y + math.cos(a) * h, z)


def stretched(cube):
    for f in cube.faces.values():
        if f is not None:
            f["stretch"] = True
    return cube


def panel(bone, name, a0, a1, b0, b1, th, region, outward, overlap=1.04):
    return stretched(board(bone, name, a0, a1, b0, b1, th, region, outward, overlap=overlap))


# ---------------------------------------------------------------- interior surfaces from the grid
OPEN_KINDS = (ni.DRY, ni.LADDER, ni.AIRLOCK)
MAX_TILE = 4  # cells (2 blocks): the texture regions are 32 px


def greedy(mask):
    """Rectangles (i0, j0, i1, j1) covering a 2D boolean mask, at most MAX_TILE cells a side."""
    m = mask.copy()
    out = []
    ni_, nj_ = m.shape
    for i in range(ni_):
        j = 0
        while j < nj_:
            if not m[i, j]:
                j += 1
                continue
            j1 = j
            while j1 + 1 < nj_ and m[i, j1 + 1] and j1 + 1 - j < MAX_TILE:
                j1 += 1
            i1 = i
            while i1 + 1 < ni_ and i1 + 1 - i < MAX_TILE and m[i1 + 1, j:j1 + 1].all():
                i1 += 1
            m[i:i1 + 1, j:j1 + 1] = False
            out.append((i, j, i1, j1))
            j = j1 + 1
    return out


def interior_surfaces(bone, outside, g):
    k = g.k
    solid = k == ni.SOLID
    opened = np.isin(k, OPEN_KINDS) | (k >= ni.DOOR)
    out = k == ni.OUT
    C = ni.CELL
    origin = (ni.X0, ni.Y0, ni.Z0)
    count = 0
    for a in range(3):
        for s in (1, -1):
            nb_open = np.zeros_like(opened)
            nb_out = np.zeros_like(out)
            src = [slice(None)] * 3
            dst = [slice(None)] * 3
            if s > 0:
                dst[a], src[a] = slice(0, -1), slice(1, None)
            else:
                dst[a], src[a] = slice(1, None), slice(0, -1)
            nb_open[tuple(dst)] = opened[tuple(src)]
            nb_out[tuple(dst)] = out[tuple(src)]
            inner = solid & nb_open
            # outside faces of the cells standing above the hull body (the wheelhouse)
            above = np.zeros_like(solid)
            if True:
                Y, Z, X = g.Y, g.Z, g.X
                top = ns.AXIS_Y + np.vectorize(ns.half_height)(Z) * np.sqrt(np.clip(1 - (X / np.maximum(1e-6, np.vectorize(ns.half_width)(Z))) ** 2, 0, 1))
                above = Y > top + 0.05
            outer = solid & nb_out & above
            if a == 1:
                mat = "floor" if s > 0 else "ceiling"
            else:
                mat = "wall"
            others = [b for b in range(3) if b != a]
            for layer, kind, region in ((inner, "lit_" + mat, mat), (outer, "tower", "plate")):
                for idx in range(layer.shape[a]):
                    sl = [slice(None)] * 3
                    sl[a] = idx
                    m2 = layer[tuple(sl)]
                    if not m2.any():
                        continue
                    plane = origin[a] + (idx + (1 if s > 0 else 0)) * C
                    for (i0, j0, i1, j1) in greedy(m2):
                        lo = [0.0, 0.0, 0.0]
                        hi = [0.0, 0.0, 0.0]
                        b0, b1 = others
                        lo[b0], hi[b0] = origin[b0] + i0 * C, origin[b0] + (i1 + 1) * C
                        lo[b1], hi[b1] = origin[b1] + j0 * C, origin[b1] + (j1 + 1) * C
                        lo[a] = hi[a] = plane + s * 0.005
                        center = [(lo[q] + hi[q]) / 2 for q in range(3)]
                        size = [max(0.01, hi[q] - lo[q]) for q in range(3)]
                        size[a] = 0.01
                        face = ("+" if s > 0 else "-") + str(a + 1)
                        if a == 1:
                            udir, vdir = v3(1, 0, 0), v3(0, 0, 1)
                        else:
                            udir, vdir = (v3(0, 0, 1) if a == 0 else v3(1, 0, 0)), v3(0, -1, 0)
                        target = bone if kind.startswith("lit") else outside
                        add_cube(target, "%s_%d" % (kind, count), center, EYE, size, {face: region}, u_dir=udir, v_dir=vdir)
                        count += 1
    return count


def ladder(bone, name, x0, x1, z_wall, y0, y1, side):
    """Rungs every half block against the wall at z_wall (side: +1 the wall is towards +z)."""
    z = z_wall - side * 0.08
    for k, x in enumerate((x0 + 0.08, x1 - 0.08)):
        beam(bone, "%s_rail_%d" % (name, k), v3(x, y0, z), v3(x, y1, z), 0.07, "rung")
    y = y0 + 0.25
    i = 0
    while y < y1 - 0.1:
        beam(bone, "%s_rung_%d" % (name, i), v3(x0 + 0.08, y, z), v3(x1 - 0.08, y, z), 0.06, "rung")
        y += 0.5
        i += 1


def build(g):
    root = Bone("nautilus")
    hull = Bone("hull", parent=root)
    rooms = Bone("rooms", parent=root)
    tail = Bone("tail", parent=root)
    fittings = Bone("fittings", parent=root)

    # ---------------------------------------------------------------- hull: elliptical body in tilted panels
    for i in range(len(HULL_S) - 1):
        za, zb = hull_z(HULL_S[i]), hull_z(HULL_S[i + 1])
        for j in range(NAZ):
            a0, a1 = 360.0 * j / NAZ, 360.0 * (j + 1) / NAZ
            am = (a0 + a1) / 2
            outward = v3(math.sin(math.radians(am)), math.cos(math.radians(am)), 0)
            region = "plate" if math.cos(math.radians(am)) > -0.35 else "plate_dark"
            panel(hull, "hull_%d_%d" % (i, j), P(za, a0), P(za, a1), P(zb, a0), P(zb, a1), 0.12, region, outward)
    # ram: a long tapering steel spike at the bow
    for k, (z0, z1, r) in enumerate(((ns.BOW_Z - 2.0, ns.BOW_Z + 1.5, 0.9), (ns.BOW_Z + 1.5, ns.BOW_Z + 4.0, 0.55),
                                     (ns.BOW_Z + 4.0, ns.RAM_TIP_Z, 0.25))):
        add_cube(hull, "ram_%d" % k, v3(0, ns.AXIS_Y, (z0 + z1) / 2), rz(math.pi / 4), (r, r, z1 - z0), "steel")
    # a few lit portholes along the sides (step 2 will place them as on the reference)
    for side in (1, -1):
        for k, z in enumerate((-18.0, -8.0, 8.0, 18.0)):
            p = P(z, side * 90, 0.06)
            add_cube(fittings, "glow_porthole_%d_%d" % (side > 0, k), p, EYE, (0.06, 0.7, 0.7), "glass")

    # ---------------------------------------------------------------- tail: shaft, propeller, fin
    beam(tail, "shaft", v3(0, ns.AXIS_Y, ns.STERN_Z + 2.0), v3(0, ns.AXIS_Y, ns.STERN_Z - 1.2), 0.5, "steel")
    prop_z = ns.STERN_Z - 0.8
    prop = Bone("propeller", origin=(0, ns.AXIS_Y, prop_z), parent=root)
    hub = v3(0, ns.AXIS_Y, prop_z)
    add_cube(prop, "prop_hub", hub, EYE, (0.8, 0.8, 0.6), "brass")
    pitch = math.radians(25)
    for k in range(4):
        a = 2 * math.pi * k / 4
        d = v3(math.sin(a), math.cos(a), 0)
        side = np.cross(v3(0, 0, 1), d)
        w = side * math.cos(pitch) + v3(0, 0, 1) * math.sin(pitch)
        n = np.cross(d, w)
        add_cube(prop, "prop_blade_%d" % k, hub + d * 1.7, np.column_stack([d, w, n]), (2.6, 1.1, 0.12), "brass")
    fin_z0, fin_z1 = ns.STERN_Z - 1.6, ns.TAIL_END_Z
    add_cube(tail, "fin", v3(0, ns.AXIS_Y, (fin_z0 + fin_z1) / 2), EYE, (0.2, 11.0, fin_z0 - fin_z1), "steel")
    beam(tail, "fin_post", v3(0, ns.AXIS_Y, ns.STERN_Z + 0.5), v3(0, ns.AXIS_Y, fin_z1), 0.35, "steel")

    # ---------------------------------------------------------------- rooms: walls, floors, ceilings on the grid
    n = interior_surfaces(rooms, hull, g)
    # ladders: up to the hatch and up into the wheelhouse
    hz0, hz1 = ni.HATCH_Z
    top = ns.hull_top((hz0 + hz1) / 2, 0.5)
    ladder(fittings, "lit_ladder_hatch", ni.HATCH_X[0], ni.HATCH_X[1], hz1, ns.MAIN_FLOOR_Y, top - ns.SHELL, 1)
    tz0, tz1 = ni.TOWER_SHAFT_Z
    ladder(fittings, "lit_ladder_tower", ni.HATCH_X[0], ni.HATCH_X[1], tz1, ns.MAIN_FLOOR_Y, ni.TOWER_FLOOR_Y + 1.0, 1)
    # hatch (door 0): a riveted lid hinged on its aft edge
    hinge = v3(0, top + 0.06, hz0)
    door = Bone("door_%d" % ni.HATCH_DOOR, origin=tuple(hinge), parent=root)
    add_cube(door, "hatch_lid", v3(0, top + 0.06, (hz0 + hz1) / 2), EYE, (1.1, 0.12, 1.1), {"all": "steel", "+2": "hatch", "-2": "hatch"})
    add_cube(door, "hatch_wheel", v3(0, top + 0.16, (hz0 + hz1) / 2), EYE, (0.5, 0.06, 0.5), "brass")
    # wheelhouse: windows and a lamp
    tower_front = ni.TOWER_Z[1]
    for k, x in enumerate((-0.9, 0.9)):
        add_cube(fittings, "glow_tower_window_%d" % k, v3(x, ni.TOWER_FLOOR_Y + 1.6, tower_front + 0.02), EYE, (0.7, 0.7, 0.04), "glass")
    add_cube(fittings, "glow_tower_lamp", v3(0, ni.TOWER_FLOOR_Y + ni.TOWER_HEIGHT + 0.7, tower_front - 0.5), EYE, (0.4, 0.4, 0.4), "glow")
    # lamps in the halls
    for z in range(-24, 28, 6):
        add_cube(fittings, "glow_hall_lamp_%d" % z, v3(0, ns.MAIN_FLOOR_Y + ns.LEVEL_HEIGHT - 0.12, z), EYE, (0.4, 0.2, 0.4), "glow")
    for z in range(-18, 20, 6):
        add_cube(fittings, "glow_lower_lamp_%d" % z, v3(0, ns.LOWER_FLOOR_Y + 4.0 - 0.12, z), EYE, (0.4, 0.2, 0.4), "glow")
    return root, n


def build_animations(root):
    kf, rot_kf, animation, find = gg.kf, gg.rot_kf, gg.animation, gg.find
    anims = []
    prop = find(root, "propeller")
    anims.append(animation("propeller", 2.0, "loop", [(prop, [
        rot_kf(t, (0, 0, a)) for t, a in ((0.0, 0), (0.5, 270), (1.0, 540), (1.5, 810), (2.0, 1080))])]))
    door = find(root, "door_%d" % ni.HATCH_DOOR)
    anims.append(animation("door_%d" % ni.HATCH_DOOR, 1.0, "hold", [(door, [rot_kf(0.0, (0, 0, 0)), rot_kf(1.0, (-110, 0, 0))])]))
    return anims


def main():
    g = ni.build()
    size = g.write(os.path.join(ROOT, ni.GRID_PATH))
    root, n = build(g)
    anims = build_animations(root)
    tex_dir = os.path.join(ROOT, "src/main/resources/assets/medievalships/textures")
    tex_path = os.path.join(tex_dir, "entity/nautilus.png")
    nt.make_texture(tex_path)
    nt.make_item_icon(os.path.join(tex_dir, "item/nautilus.png"))
    with open(tex_path, "rb") as f:
        png = f.read()
    textures = [gn.texture_entry("nautilus.png", nt.SIZE, png, "entity", "nautilus.png")]
    textures[0]["id"] = "0"
    model = gn.export(root, anims, textures, [
        os.path.join(ROOT, "blockbench/nautilus.bbmodel"),
        os.path.join(ROOT, "src/main/resources/assets/medievalships/models/entity/nautilus.bbmodel"),
    ], name="nautilus", visible_box=(100, 30, 0))
    print("grid bytes:", size, "room surfaces:", n, "cubes:", len(model["elements"]),
          "animations:", [a["name"] for a in model["animations"]])


if __name__ == "__main__":
    main()
