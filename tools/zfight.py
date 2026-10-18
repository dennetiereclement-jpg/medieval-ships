#!/usr/bin/env python3
"""Finds and removes z-fighting in a generated model.

Two visible faces that lie in the same plane and overlap flicker in game ("z-fighting"); the
renderer draws both sides of every face (entityCutoutNoCull), so a face fights with a coplanar
face of either direction, and a cube that is flat (zero thickness) fights with itself.

    fix(root)      before export: pushes the smaller of two fighting faces slightly outwards
                   (a hundredth of a block, invisible) and gives flat cubes a minimal thickness;
                   returns the number of faces moved
    report(root)   list of the fighting pairs that remain

Usage:  python3 tools/zfight.py galley|galleon|warship|medieval_galley|paddleboat|elven
        (builds the model with its generator, without writing it, and prints what fights)
"""
import importlib
import sys
from collections import defaultdict

import numpy as np

TOL = 0.006    # faces closer than this fight at a distance (24-bit depth buffer)
PUSH = 0.012   # how far the losing face is moved out
MIN_TH = 0.012  # minimal thickness of a flat cube
AXES = {"+1": (0, 1), "-1": (0, -1), "+2": (1, 1), "-2": (1, -1), "+3": (2, 1), "-3": (2, -1)}
SEMANTIC_FACE = {"+1": "west", "-1": "east", "+2": "up", "-2": "down", "+3": "north", "-3": "south"}


def _cubes(root):
    stack = [root]
    while stack:
        b = stack.pop()
        yield from b.cubes
        stack.extend(b.children)


def _faces(root):
    out = []
    for c in _cubes(root):
        R = c.bone.frame_rot() @ np.asarray(c.axes, dtype=float)
        C = c.bone.to_world(np.asarray(c.center, dtype=float))
        half = np.asarray(c.size, dtype=float) / 2
        for sem, (k, s) in AXES.items():
            if c.faces.get(SEMANTIC_FACE[sem]) is None:
                continue
            n = R[:, k] * s
            p = C + n * half[k]
            o = [j for j in range(3) if j != k]
            e1, e2 = R[:, o[0]] * half[o[0]], R[:, o[1]] * half[o[1]]
            area = 4 * half[o[0]] * half[o[1]]
            if area < 1e-6:
                continue
            out.append(dict(cube=c, sem=sem, k=k, n=n, p=p, e1=e1, e2=e2, area=area))
    return out


def _overlap(f, g):
    """Do the two coplanar rectangles overlap (by more than a sliver)?  Separating axis test in the plane."""
    def corners(h):
        return [h["p"] + a * h["e1"] + b * h["e2"] for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    cf, cg = corners(f), corners(g)
    for h in (f, g):
        for e in (h["e1"], h["e2"]):
            L = np.linalg.norm(e)
            if L < 1e-9:
                continue
            ax = e / L
            pf = [np.dot(q, ax) for q in cf]
            pg = [np.dot(q, ax) for q in cg]
            if min(pf) > max(pg) - 0.012 or min(pg) > max(pf) - 0.012:
                return False
    return True


def find(root):
    faces = _faces(root)
    buckets = defaultdict(list)
    for i, f in enumerate(faces):
        n = f["n"]
        # one key for both directions: the normal made canonical (first non-zero component positive)
        sgn = 1
        for x in n:
            if abs(x) > 1e-3:
                sgn = 1 if x > 0 else -1
                break
        cn = n * sgn
        f["cn"], f["d"] = cn, float(np.dot(cn, f["p"]))
        buckets[tuple(np.round(cn * 40).astype(int))].append(i)
    pairs = []
    for idx in buckets.values():
        idx.sort(key=lambda i: faces[i]["d"])
        for a in range(len(idx)):
            f = faces[idx[a]]
            for b in range(a + 1, len(idx)):
                g = faces[idx[b]]
                if g["d"] - f["d"] > TOL:
                    break
                if f["cube"] is g["cube"]:
                    continue
                if abs(np.dot(f["cn"], g["cn"])) < 0.9995:
                    continue
                if _overlap(f, g):
                    pairs.append((f, g))
    flat = []
    for c in _cubes(root):
        for k in range(3):
            if c.size[k] < TOL:
                o = [j for j in range(3) if j != k]
                if c.size[o[0]] * c.size[o[1]] > 1e-6:
                    flat.append((c, k))
    return pairs, flat


def fix(root, passes=30):
    moved = 0
    for _ in range(passes):
        pairs, flat = find(root)
        for c, k in flat:
            c.size = np.asarray(c.size, dtype=float).copy()
            c.size[k] = MIN_TH
            moved += 1
        if not pairs:
            if not flat:
                break
            continue
        # colour the conflict graph (largest faces first, they stay put); each colour is one more
        # step outwards, so faces that overlap never end up in the same plane again
        nodes, adj = {}, defaultdict(set)
        for f, g in pairs:
            kf, kg = (id(f["cube"]), f["sem"]), (id(g["cube"]), g["sem"])
            nodes[kf], nodes[kg] = f, g
            adj[kf].add(kg)
            adj[kg].add(kf)
        colour = {}
        for key in sorted(nodes, key=lambda q: (-nodes[q]["area"], nodes[q]["cube"].name, nodes[q]["sem"])):
            used = {colour[n] for n in adj[key] if n in colour}
            c = 0
            while c in used:
                c += 1
            colour[key] = c
        for key, col in colour.items():
            if col == 0:
                continue
            w = nodes[key]
            c, k = w["cube"], w["k"]
            s = AXES[w["sem"]][1]
            ax = np.asarray(c.axes, dtype=float)[:, k]
            c.size = np.asarray(c.size, dtype=float).copy()
            c.size[k] += PUSH * col
            c.center = np.asarray(c.center, dtype=float) + ax * s * PUSH * col / 2
            moved += 1
    left = len(find(root)[0])
    if left:
        print("zfight: %d coplanar face pairs left" % left)
    return moved


def report(root):
    pairs, flat = find(root)
    return [(f["cube"].name, f["sem"], g["cube"].name, g["sem"]) for f, g in pairs], [(c.name, k) for c, k in flat]


if __name__ == "__main__":
    sys.path.insert(0, __file__.rsplit("/", 1)[0])
    mod = {"galley": "generate_galley", "galleon": "generate_galleon", "warship": "generate_warship",
           "medieval_galley": "generate_medieval_galley", "paddleboat": "generate_paddleboat", "elven": "generate_elven"}[sys.argv[1]]
    m = importlib.import_module(mod)
    root = m.build()
    root = root[0] if isinstance(root, tuple) else root
    if "--fix" in sys.argv:
        print("moved %d faces" % fix(root))
    pairs, flat = report(root)
    print("%s: %d fighting pairs, %d flat cubes" % (sys.argv[1], len(pairs), len(flat)))
    for p in pairs[: 25]:
        print("  %s %s  <->  %s %s" % p)
    for f in flat[:10]:
        print("  flat %s axis %d" % f)
