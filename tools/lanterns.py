"""Every lantern of every ship drawn like the steam paddleboat's.

convert(root), called on export, finds each lantern body (a cube whose four sides use the
"lantern" region, painted as lit glass by galley_texture.paint_lamp_glass) and rebuilds it in the
same box: lit glass drawn full bright (its name starts with "glow"), thin corner posts, base plate,
cap, small dome, gold finial and carrying ring, in the metal of the old lantern's top (iron or
gold). The old inner glow cube, now hidden inside the glass, is removed.
"""
import numpy as np

import generate_galley as gg

SIDES = ("north", "south", "east", "west")


def _all_cubes(b):
    yield from list(b.cubes)
    for ch in b.children:
        yield from _all_cubes(ch)


def _region(face):
    return None if face is None else face["region"]


def convert(root):
    bodies = [c for c in _all_cubes(root)
              if all(_region(c.faces.get(f)) == "lantern" for f in SIDES) and not c.name.startswith("glow")]
    for c in bodies:
        bone = c.bone
        metal = _region(c.faces.get("up")) or _region(c.faces.get("down")) or "gold"
        C = bone.to_world(np.asarray(c.center, dtype=float))
        R = bone.frame_rot() @ np.asarray(c.axes, dtype=float)
        w = float(min(c.size[0], c.size[2]))
        h = float(c.size[1])
        # the old glow cube inside the body
        for g in list(bone.cubes):
            if g is not c and g.name.startswith("glow") and np.linalg.norm(bone.to_world(np.asarray(g.center, dtype=float)) - C) < 0.5 * h:
                bone.cubes.remove(g)
        bone.cubes.remove(c)
        up = R[:, 1]
        name = c.name

        def box(n, centre, size, reg, **kw):
            return gg.add_cube(bone, n, centre, R, size, reg, **kw)
        gh = 0.8 * h
        box("glow_" + name, C, (0.82 * w, gh, 0.82 * w), {"all": "lantern", "+2": metal, "-2": metal}, stretch=True)
        for i, (dx, dz) in enumerate(((1, 1), (1, -1), (-1, 1), (-1, -1))):
            box("%s_post_%d" % (name, i), C + R @ np.array([dx * 0.41 * w, 0, dz * 0.41 * w]),
                (0.12 * w, gh + 0.02 * h, 0.12 * w), metal)
        box(name + "_base", C - up * (gh / 2 + 0.05 * h), (w, 0.1 * h, w), metal)
        box(name + "_cap", C + up * (gh / 2 + 0.05 * h), (1.06 * w, 0.1 * h, 1.06 * w), metal)
        box(name + "_dome", C + up * (gh / 2 + 0.16 * h), (0.7 * w, 0.14 * h, 0.7 * w), metal)
        box(name + "_finial", C + up * (gh / 2 + 0.28 * h), (0.2 * w, 0.12 * h, 0.2 * w), "gold")
        top = C + up * (gh / 2 + 0.38 * h)
        gg.beam(bone, name + "_ring", top - R[:, 0] * 0.22 * w, top + R[:, 0] * 0.22 * w, 0.07 * w, metal)
    return len(bodies)
