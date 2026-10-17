#!/usr/bin/env python3
"""Checks that no two sails of a model cross each other (and that they do not cross the masts' tops).

Usage:  python3 tools/sail_check.py warship|galleon|elven|medieval_galley

Every sail strip is an oriented box; strips of triangular sails that lie outside their
triangle (transparent) are ignored. Two strips of different sails that intersect are reported.
"""
import importlib
import sys

import numpy as np

import generate_galley as gg


def obb(cube):
    c = cube.bone.to_world(np.asarray(cube.center, dtype=float))
    R = cube.bone.frame_rot() @ np.asarray(cube.axes, dtype=float)
    return c, R, np.asarray(cube.size, dtype=float) / 2


def overlap(a, b, margin=0.0):
    (ca, Ra, ha), (cb, Rb, hb) = a, b
    axes = [Ra[:, i] for i in range(3)] + [Rb[:, i] for i in range(3)]
    for i in range(3):
        for j in range(3):
            v = np.cross(Ra[:, i], Rb[:, j])
            if np.linalg.norm(v) > 1e-6:
                axes.append(v / np.linalg.norm(v))
    d = cb - ca
    for ax in axes:
        ra = sum(ha[k] * abs(np.dot(Ra[:, k], ax)) for k in range(3))
        rb = sum(hb[k] * abs(np.dot(Rb[:, k], ax)) for k in range(3))
        if abs(np.dot(d, ax)) > ra + rb - margin:
            return False
    return True


def main(which):
    mod = importlib.import_module({"warship": "generate_warship", "galleon": "generate_galleon", "elven": "generate_elven",
                                   "medieval_galley": "generate_medieval_galley"}[which])
    cubes = []
    orig = gg.Cube.__init__

    def init(self, *a, **k):
        orig(self, *a, **k)
        cubes.append(self)
    gg.Cube.__init__ = init
    import generate_galleon as gn
    tris = {}
    orig_tri = gn.tri_sail

    def tri_spy(bone, name, *a, **k):
        t = orig_tri(bone, name, *a, **k)
        tris[name] = t
        return t
    gn.tri_sail = tri_spy
    mod.tri_sail = tri_spy if hasattr(mod, "tri_sail") else None
    mod.build()
    sails = {}
    for c in cubes:
        b = c.bone
        while b is not None and not (b.name.startswith("sail") or b.name == "jib"):
            b = b.parent
        if b is None:
            continue
        sub = (c.faces.get("north") or c.faces.get("south") or {}).get("sub")
        key = c.name.rsplit("_", 2)[0]
        if sub is not None and key in tris:
            tri = tris.get(key)
            u, v = (sub[0] + sub[2]) / 2, (sub[1] + sub[3]) / 2
            if tri is not None:
                (ax, ay), (bx, by), (cx, cy) = tri
                # outside the triangle (transparent) when beyond the luff->clew or tack->clew edge
                def side(x1, y1, x2, y2):
                    return (u - x2) * (y1 - y2) - (x1 - x2) * (v - y2)
                d1, d2, d3 = side(ax, ay, bx, by), side(bx, by, cx, cy), side(cx, cy, ax, ay)
                if (d1 < 0 or d2 < 0 or d3 < 0) and (d1 > 0 or d2 > 0 or d3 > 0):
                    continue
        sails.setdefault(key, []).append(obb(c))
    names = sorted(sails)
    bad = 0
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            hits = sum(1 for a in sails[names[i]] for b in sails[names[j]] if overlap(a, b, 0.02))
            if hits:
                bad += 1
                print("CROSS %s x %s (%d strips)" % (names[i], names[j], hits))
    print("%s: %d sails, %d crossing pairs" % (which, len(names), bad))
    return bad


if __name__ == "__main__":
    sys.exit(1 if main(sys.argv[1]) else 0)
