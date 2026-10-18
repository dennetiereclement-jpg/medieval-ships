"""Ropes made fast to a sail follow it when it is furled.

A sheet (or a tack) runs from a corner of the sail down to the deck. When the sail is furled (animation
sail_furl: the sail bone is scaled towards its yard) the clew goes up to the yard, and a rope that
stayed put would end in thin air. follow(root, anims), called on export, finds every sheet and tack
with one end on a furling sail, gives it its own bone pivoting on its fixed end, and adds to sail_furl a
rotation and a scale of that bone so that its free end stays on the clew all the way up.
"""
import math

import numpy as np

import generate_galley as gg

MOVES = 0.25    # ends that move less than this when furled are left alone


def _cubes(b):
    yield from ((c, b) for c in b.cubes)
    for ch in b.children:
        yield from _cubes(ch)


def _world_obb(c):
    R = c.bone.frame_rot() @ np.asarray(c.axes, dtype=float)
    C = c.bone.to_world(np.asarray(c.center, dtype=float))
    return C, R, np.asarray(c.size, dtype=float) / 2


def _dist_to_obb(p, obb):
    C, R, h = obb
    q = R.T @ (p - C)
    d = np.maximum(np.abs(q) - h, 0)
    return float(np.linalg.norm(d))


def _nearest_on_obb(p, obb):
    C, R, h = obb
    q = np.clip(R.T @ (p - C), -h, h)
    return C + R @ q


SHEET_REACH = 2.0  # a sheet's upper end may sit a little off the cloth (belly, bolt rope)


def _furled(bone, scale, p):
    """World position of the point p (world, rest) of the bone once its scale keyframe applies."""
    q = bone.to_frame(p)
    q = bone.rot @ ((q - bone.origin) * scale) + bone.origin
    for g in bone.chain()[1:]:
        q = g.rot @ (q - g.origin) + g.origin
    return q


def _rotation(a, b):
    """Smallest rotation taking the unit vector a onto the unit vector b."""
    v = np.cross(a, b)
    s, c = np.linalg.norm(v), float(np.dot(a, b))
    if s < 1e-9:
        return np.eye(3)
    k = v / s
    K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    ang = math.atan2(s, c)
    return np.eye(3) + math.sin(ang) * K + (1 - math.cos(ang)) * K @ K


def _find_bone(root, uuid):
    if root.uuid == uuid:
        return root
    for ch in root.children:
        r = _find_bone(ch, uuid)
        if r is not None:
            return r
    return None


def follow(root, anims):
    furl = next((a for a in anims if a["name"] == "sail_furl"), None)
    if furl is None:
        return 0
    sails = []
    for uuid, anim in list(furl["animators"].items()):
        scales = [k for k in anim["keyframes"] if k["channel"] == "scale"]
        if not scales:
            continue
        last = max(scales, key=lambda k: k["time"])
        first = min(scales, key=lambda k: k["time"])
        d = last["data_points"][0]
        s = np.array([abs(float(d["x"])), abs(float(d["y"])), abs(float(d["z"]))])
        bone = _find_bone(root, uuid)
        if bone is None:
            continue
        obbs = [_world_obb(c) for c, _ in _cubes(bone) if not c.name.startswith("rope")]
        sails.append((bone, s, obbs, first["time"], last["time"]))
    if not sails:
        return 0
    sail_bones = {id(b) for b, *_ in sails}

    def inside_sail(b):
        while b is not None:
            if id(b) in sail_bones:
                return True
            b = b.parent
        return False

    # only the running rigging made fast to a corner of the cloth (sheets, tacks): stays and shrouds
    # run close to the jibs but do not move with them
    ropes = [(c, b) for c, b in _cubes(root)
             if ("sheet" in c.name or "tack" in c.name) and not inside_sail(b) and not c.name.startswith("rope_furl_")]
    # parts that stay where they are when the sails furl (boom, rails...): a rope end on one of them
    # is made fast there, not to the cloth (the elven mainsheet hangs from the boom)
    rigging = ("rope", "sheet", "tack", "brace", "stay", "shroud", "ratline", "halyard", "lift", "chain", "deadeye")
    static = [_world_obb(c) for c, b in _cubes(root) if not inside_sail(b) and not any(r in c.name for r in rigging)]
    moved = 0
    for c, b in ropes:
        C, R, h = _world_obb(c)
        ends = [C - R[:, 0] * h[0], C + R[:, 0] * h[0]]
        hits = []
        for e in ends:
            best = None
            if any(_dist_to_obb(e, o) < 0.05 for o in static):
                hits.append(None)
                continue
            for sb, s, obbs, t0, t1 in sails:
                if not obbs:
                    continue
                d, o = min(((_dist_to_obb(e, o), o) for o in obbs), key=lambda x: x[0])
                if d < SHEET_REACH and (best is None or d < best[3]):
                    e2 = _furled(sb, s, _nearest_on_obb(e, o))
                    if np.linalg.norm(e2 - e) > MOVES:
                        best = (e2, t0, t1, d)
            hits.append(best)
        if hits[0] is not None and hits[1] is not None:
            # a sheet is made fast to one sail only: the end nearer to its cloth
            hits[0 if hits[0][3] > hits[1][3] else 1] = None
        if (hits[0] is None) == (hits[1] is None):
            continue  # fixed at both ends (or tied to two sails): left as it is
        fixed, free = (0, 1) if hits[1] is not None else (1, 0)
        A, E = ends[fixed], ends[free]
        E2, t0, t1, _ = hits[free]
        k = np.linalg.norm(E2 - A) / np.linalg.norm(E - A)
        Rw = _rotation((E - A) / np.linalg.norm(E - A), (E2 - A) / np.linalg.norm(E2 - A))
        # the rope gets its own bone pivoting on its fixed end (no rotation at rest: same frame as the ship)
        nb = gg.Bone("rope_furl_" + c.name.replace("rope_", "", 1), origin=tuple(A), parent=root)
        b.cubes.remove(c)
        c.center = C
        c.axes = R
        c.bone = nb
        nb.cubes.append(c)
        e = gg.matrix_to_euler_zyx(gg.to_bb_rot(Rw))
        furl["animators"][nb.uuid] = {"name": nb.name, "type": "bone", "keyframes": [
            gg.rot_kf(t0, (0, 0, 0)), gg.rot_kf(t1, tuple(e)),
            gg.kf("scale", t0, (1, 1, 1)), gg.kf("scale", t1, (k, k, k))]}
        moved += 1
    return moved
