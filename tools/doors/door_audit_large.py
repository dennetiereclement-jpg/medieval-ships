#!/usr/bin/env python3
"""Automated audit of the three LARGE doors (porte_chateau, porte_vapeur_grande, porte_entrepot), 1.32.0.

It reads the exported .bbmodel (what the game draws) and the door's texture, and counts:

  1. holes      orthographic coverage renders at PPB px per block (default 64, i.e. 1 px = 1/64 block), on a
                magenta background: whole door closed (front, back), each leaf alone (front, back, both edges).
                The cut-out sprites and the `detail` bones (hidden in game beyond ~32 blocks) are left OUT of
                these renders, so they never plug a hole. Whole door: every background pixel inside the
                4 x 6 rectangle is a hole, except the declared silhouette notches (crenels, open to the top
                edge). A leaf alone: every background pixel enclosed by the leaf or spanned by it (covered
                pixels above and below in its column and left and right in its row).
  2. alpha      faces of solid cubes (every cube whose name does not start with "cut_") that map texels with
                alpha < 255; cut-out sprites must be offset by >= 1/64 block from any parallel face (point 3).
  3. coplanar   pairs of parallel faces (either direction: the game draws both sides, entityCutoutNoCull) that
                overlap and lie in the same plane (<= 1e-4 block) or closer than 1/64 block, closed and open
                90 degrees backwards and forwards; cubes thinner than 1/64 block.
  4. contract   bounds (4 x 6 x 1 box), leaf pivots, leaf / frame and leaf / leaf sweep 0 -> 90 degrees.

    import door_audit_large as A
    rep = A.audit(model, tex_rgba, notches=[(X0, X1, Y0, Y1), ...], verbose=True)   # door px for the notches
    python3 tools/doors/door_audit_large.py porte_chateau [--dump]                   # audit the files on disk
"""
import copy
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, TOOLS)
import preview as pv  # noqa: E402

ROOT = os.path.abspath(os.path.join(TOOLS, ".."))
ASSETS = os.path.join(ROOT, "src/main/resources/assets/medievalships")
P = 1.0 / 16
COP = 1e-4                 # same plane
MIN_GAP = 1.0 / 64         # parallel overlapping faces must be at least this far apart
OVL = 1e-4                 # overlap needed (block) along both in-plane axes to count as overlapping
ALPHA_CUT = 26             # the game's cutout threshold (alpha < 0.1 discarded)
PIVOTS = {"leaf_l": (-1.625, 0.0), "leaf_r": (1.625, 0.0)}
BOX_LO, BOX_HI = np.array([-2.0, 0.0, -0.5]), np.array([2.0, 6.0, 0.5])
FN = {"north": (2, -1), "south": (2, 1), "west": (0, -1), "east": (0, 1), "up": (1, 1), "down": (1, -1)}


# ------------------------------------------------------------------ model -> faces
def with_rot(model, rots):
    m = copy.deepcopy(model)

    def walk(g):
        if g["name"] in rots:
            g["rotation"] = list(rots[g["name"]])
        for c in g["children"]:
            if isinstance(c, dict):
                walk(c)
    for g in m["outliner"]:
        walk(g)
    return m


POSES = {"fermee": {}, "ouverte_arriere": {"leaf_l": [0, 90, 0], "leaf_r": [0, -90, 0]},
         "ouverte_avant": {"leaf_l": [0, -90, 0], "leaf_r": [0, 90, 0]}}


def faces_of(model, rots=None):
    """Every textured face: dict(el, chain (names, innermost first), group, fname, corners (4 x 3, door blocks),
    uvs, n (outward unit normal), d (= n . p), centre, glow)."""
    m = with_rot(model, rots) if rots else model
    elements = {e["uuid"]: e for e in m["elements"]}
    out = []

    def tf(p, chain):
        for g in chain:
            o = np.array(g["origin"], float)
            R = pv.rot_zyx(np.array(g.get("rotation", [0, 0, 0]), float))
            p = R @ (p - o) + o
        return p

    def door(p):
        return np.array([-p[0] / 16, p[1] / 16, -p[2] / 16])

    def emit(e, chain):
        f, t = np.array(e["from"], float), np.array(e["to"], float)
        o = np.array(e.get("origin", [0, 0, 0]), float)
        R = pv.rot_zyx(e.get("rotation", [0, 0, 0]))
        names = [g["name"] for g in chain]
        group = next((nm for nm in names if nm in ("leaf_l", "leaf_r", "frame")), "frame")
        ctr = door(tf(R @ ((f + t) / 2 - o) + o, chain))
        for fname, face in e["faces"].items():
            if face.get("texture") is None:
                continue
            n_bb, ud, vd = [np.array(x, float) for x in pv.FACES[fname]]
            corners, uvs = [], []
            u1, v1, u2, v2 = face["uv"]
            for cu, cv in ((0, 0), (1, 0), (1, 1), (0, 1)):
                p = np.empty(3)
                for ax in range(3):
                    if n_bb[ax] != 0:
                        p[ax] = t[ax] if n_bb[ax] > 0 else f[ax]
                    elif ud[ax] != 0:
                        lo, hi = (f[ax], t[ax]) if ud[ax] > 0 else (t[ax], f[ax])
                        p[ax] = lo + (hi - lo) * cu
                    else:
                        lo, hi = (f[ax], t[ax]) if vd[ax] > 0 else (t[ax], f[ax])
                        p[ax] = lo + (hi - lo) * cv
                corners.append(door(tf(R @ (p - o) + o, chain)))
                uvs.append((u1 + (u2 - u1) * cu, v1 + (v2 - v1) * cv))
            corners = np.array(corners)
            nrm = np.cross(corners[1] - corners[0], corners[3] - corners[0])
            L = np.linalg.norm(nrm)
            fc = corners.mean(0)
            if L < 1e-12:
                # degenerate face (zero-size cube along an in-plane axis): normal from the cube centre
                continue
            nrm /= L
            if np.dot(nrm, fc - ctr) < 0:
                nrm = -nrm
            out.append(dict(el=e["name"], uuid=e["uuid"], chain=names, group=group, fname=fname, corners=corners,
                            uvs=uvs, n=nrm, d=float(np.dot(nrm, fc)), centre=fc, glow=e["name"].startswith("glow"),
                            size=(t - f) / 16))

    def walk(g, chain):
        chain = [g] + chain
        for ch in g["children"]:
            if isinstance(ch, dict):
                walk(ch, chain)
            else:
                emit(elements[ch], chain)
    for g in m["outliner"]:
        walk(g, [])
    return out


def _axes(f):
    c = f["corners"]
    a, b = c[1] - c[0], c[3] - c[0]
    return [a / max(1e-12, np.linalg.norm(a)), b / max(1e-12, np.linalg.norm(b))]


def overlap(f, g, eps=OVL):
    """Do two parallel rectangles overlap (projected on f's plane) by more than eps along every axis?"""
    for ax in _axes(f) + _axes(g):
        pf = f["corners"] @ ax
        pg = g["corners"] @ ax
        if min(pf.max(), pg.max()) - max(pf.min(), pg.min()) <= eps:
            return False
    return True


def contains(f, g, eps=1e-4):
    """Is rectangle f inside rectangle g (both parallel)?"""
    for ax in _axes(g):
        pf, pg = f["corners"] @ ax, g["corners"] @ ax
        if pf.min() < pg.min() - eps or pf.max() > pg.max() + eps:
            return False
    return True


def parallel_pairs(faces, gap=MIN_GAP):
    """Pairs of parallel overlapping faces of different cubes closer than `gap` (both directions)."""
    buckets = {}
    for i, f in enumerate(faces):
        n = f["n"]
        sgn = 1
        for x in n:
            if abs(x) > 1e-3:
                sgn = 1 if x > 0 else -1
                break
        cn = n * sgn
        f["_cd"] = float(np.dot(cn, f["centre"]))
        buckets.setdefault(tuple(np.round(cn * 2000).astype(int)), []).append(i)
    pairs = []
    for idx in buckets.values():
        idx.sort(key=lambda i: faces[i]["_cd"])
        for a in range(len(idx)):
            f = faces[idx[a]]
            for b in range(a + 1, len(idx)):
                g = faces[idx[b]]
                dd = g["_cd"] - f["_cd"]
                if dd >= gap - 1e-6:
                    break
                if f["uuid"] == g["uuid"]:
                    continue
                if abs(np.dot(f["n"], g["n"])) < 0.99999:
                    continue
                if overlap(f, g):
                    pairs.append((f, g, abs(dd)))
    return pairs


def thin_cubes(model):
    out = []
    for e in model["elements"]:
        s = np.abs(np.array(e["to"], float) - np.array(e["from"], float)) / 16
        faces = [k for k, v in e["faces"].items() if v.get("texture") is not None]
        for k, (a, b) in enumerate((("west", "east"), ("down", "up"), ("north", "south"))):
            if s[k] < MIN_GAP - 1e-6 and (a in faces or b in faces) and (a in faces and b in faces):
                out.append((e["name"], k, round(s[k] * 16, 3)))
    return out


# ------------------------------------------------------------------ alpha
def alpha_defects(model, tex):
    """Solid cubes (name not starting with cut_) whose faces map texels with alpha < 255."""
    H, W = tex.shape[:2]
    bad = []
    for e in model["elements"]:
        if e["name"].startswith("cut_"):
            continue
        for fname, face in e["faces"].items():
            if face.get("texture") is None:
                continue
            u1, v1, u2, v2 = face["uv"]
            a0, a1 = sorted((u1, u2))
            b0, b1 = sorted((v1, v2))
            i0, i1 = int(math.floor(a0 + 1e-4)), int(math.ceil(a1 - 1e-4))
            j0, j1 = int(math.floor(b0 + 1e-4)), int(math.ceil(b1 - 1e-4))
            i1, j1 = max(i1, i0 + 1), max(j1, j0 + 1)
            sub = tex[max(0, j0):min(H, j1), max(0, i0):min(W, i1), 3]
            if sub.size == 0 or sub.min() < 255:
                bad.append((e["name"], fname, int((sub < 255).sum()) if sub.size else -1))
    return bad


# ------------------------------------------------------------------ coverage renders
VIEWS = {   # (image u axis (door coord, sign), image v axis (door coord, sign: rows go DOWN), depth axis)
    "front": ((0, 1), (1, -1)),
    "back": ((0, -1), (1, -1)),
    "edge_left": ((2, 1), (1, -1)),     # seen from -x
    "edge_right": ((2, -1), (1, -1)),   # seen from +x
}


def coverage(faces, tex, view, lo, hi, ppb=64):
    """Boolean coverage (opaque fragment) of the faces seen along `view`, over the door rectangle lo..hi (2 tuples
    in image-axis door coords: (u_lo, v_lo), (u_hi, v_hi)). Pixel centres sampled, alpha >= ALPHA_CUT."""
    (ua, us), (va, vs) = VIEWS[view]
    Wp, Hp = int(round((hi[0] - lo[0]) * ppb)), int(round((hi[1] - lo[1]) * ppb))
    cov = np.zeros((Hp, Wp), bool)
    th, tw = tex.shape[:2]
    for f in faces:
        c = f["corners"]
        U = (c[:, ua] * us - lo[0]) * ppb
        V = (hi[1] - c[:, va]) * ppb
        uv = np.array(f["uvs"], float)
        for tri in ((0, 1, 2), (0, 2, 3)):
            ax, ay = U[list(tri)], V[list(tri)]
            det = (ay[1] - ay[2]) * (ax[0] - ax[2]) + (ax[2] - ax[1]) * (ay[0] - ay[2])
            if abs(det) < 1e-9:
                continue
            x0, x1 = int(max(0, math.floor(ax.min()))), int(min(Wp - 1, math.ceil(ax.max())))
            y0, y1 = int(max(0, math.floor(ay.min()))), int(min(Hp - 1, math.ceil(ay.max())))
            if x0 > x1 or y0 > y1:
                continue
            xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
            w0 = ((ay[1] - ay[2]) * (xs - ax[2]) + (ax[2] - ax[1]) * (ys - ay[2])) / det
            w1 = ((ay[2] - ay[0]) * (xs - ax[2]) + (ax[0] - ax[2]) * (ys - ay[2])) / det
            w2 = 1 - w0 - w1
            m = (w0 >= -1e-7) & (w1 >= -1e-7) & (w2 >= -1e-7)
            if not m.any():
                continue
            tu = w0 * uv[tri[0], 0] + w1 * uv[tri[1], 0] + w2 * uv[tri[2], 0]
            tv = w0 * uv[tri[0], 1] + w1 * uv[tri[1], 1] + w2 * uv[tri[2], 1]
            tx = np.clip(np.floor(tu).astype(int), 0, tw - 1)
            ty = np.clip(np.floor(tv).astype(int), 0, th - 1)
            m &= tex[ty, tx, 3] >= ALPHA_CUT
            cov[y0:y1 + 1, x0:x1 + 1] |= m
    return cov


def enclosed(cov):
    """Uncovered pixels not connected (4-neighbours) to the image border."""
    free = np.pad(~cov, 1, constant_values=True)
    reach = np.zeros_like(free)
    reach[0, :] = reach[-1, :] = True
    reach[:, 0] = reach[:, -1] = True
    reach &= free
    while True:
        grow = reach.copy()
        grow[1:, :] |= reach[:-1, :]
        grow[:-1, :] |= reach[1:, :]
        grow[:, 1:] |= reach[:, :-1]
        grow[:, :-1] |= reach[:, 1:]
        grow &= free
        if np.array_equal(grow, reach):
            break
        reach = grow
    return (free & ~reach)[1:-1, 1:-1]


def spanned(cov):
    """Uncovered pixels with covered pixels above and below in their column AND left and right in their row."""
    up = np.maximum.accumulate(cov, axis=0)
    down = np.maximum.accumulate(cov[::-1], axis=0)[::-1]
    left = np.maximum.accumulate(cov, axis=1)
    right = np.maximum.accumulate(cov[:, ::-1], axis=1)[:, ::-1]
    return (~cov) & up & down & left & right


def leaf_holes(cov):
    return (~cov) & (enclosed(cov) | spanned(cov))


# ------------------------------------------------------------------ sweep
def _boxes(model, rots, groups):
    """Oriented boxes (centre, axes 3x3, half sizes) of the elements of the given top groups, door blocks."""
    out = []
    faces = faces_of(model, rots)
    by = {}
    for f in faces:
        by.setdefault(f["uuid"], []).append(f)
    for uid, fl in by.items():
        if fl[0]["group"] not in groups:
            continue
        pts = np.vstack([f["corners"] for f in fl])
        out.append((fl[0]["el"], fl[0]["group"], pts))
    return out


def _el_boxes(model, groups, rots=None):
    """Exact oriented boxes from the elements: (name, group, centre, A (columns = axes), half)."""
    m = with_rot(model, rots) if rots else model
    elements = {e["uuid"]: e for e in m["elements"]}
    Mf = np.diag([-1.0, 1.0, -1.0])
    out = []

    def walk(g, chain):
        chain = [g] + chain
        for ch in g["children"]:
            if isinstance(ch, dict):
                walk(ch, chain)
                continue
            e = elements[ch]
            names = [x["name"] for x in chain]
            group = next((nm for nm in names if nm in ("leaf_l", "leaf_r", "frame")), "frame")
            if group not in groups:
                continue
            f, t = np.array(e["from"], float), np.array(e["to"], float)
            o = np.array(e.get("origin", [0, 0, 0]), float)
            R = pv.rot_zyx(e.get("rotation", [0, 0, 0]))
            c = R @ ((f + t) / 2 - o) + o
            Rt = R
            for gg in chain:
                og = np.array(gg["origin"], float)
                Rg = pv.rot_zyx(np.array(gg.get("rotation", [0, 0, 0]), float))
                c = Rg @ (c - og) + og
                Rt = Rg @ Rt
            out.append((e["name"], group, Mf @ c / 16, Mf @ Rt @ Mf, np.abs(t - f) / 32))
    for g in m["outliner"]:
        walk(g, [])
    return out


def _sample_points(c, A, h, n=5):
    lin = [np.linspace(-1, 1, n if h[k] * 16 > 1.0 else 2) for k in range(3)]
    g = np.array(np.meshgrid(*lin, indexing="ij")).reshape(3, -1).T
    return c + (g * h) @ A.T


def _inside(pts, box, tol):
    _, _, c, A, h = box
    loc = (pts - c) @ A
    d = h - np.abs(loc)
    ins = np.all(d > tol, axis=1)
    return ins, np.where(ins, d.min(axis=1), 0)


def sweep(model, backwards=True, tol=1.0 / 64, step=3):
    """Leaf / frame and leaf / leaf penetrations deeper than tol (block) while the leaves swing 0 -> 90 degrees
    together: list of (a, b, worst depth px, degree)."""
    hits = {}
    frame = _el_boxes(model, ("frame",))
    sg = 1 if backwards else -1
    for deg in range(step, 91, step):
        rots = {"leaf_l": [0, deg * sg, 0], "leaf_r": [0, -deg * sg, 0]}
        leaves = _el_boxes(model, ("leaf_l", "leaf_r"), rots)
        pts = {b[0] + "@" + b[1]: (b, _sample_points(b[2], b[3], b[4])) for b in leaves}
        for key, (lb, pp) in pts.items():
            for fb in frame:
                if np.linalg.norm(fb[2] - lb[2]) > np.linalg.norm(fb[4]) + np.linalg.norm(lb[4]) + 0.01:
                    continue
                ins, dep = _inside(pp, fb, tol)
                if ins.any():
                    k = (lb[0], fb[0])
                    dpx = float(dep.max()) * 16
                    if dpx > hits.get(k, (0, 0))[0]:
                        hits[k] = (dpx, deg)
            for ob in leaves:
                if ob[1] == lb[1]:
                    continue
                if np.linalg.norm(ob[2] - lb[2]) > np.linalg.norm(ob[4]) + np.linalg.norm(lb[4]) + 0.01:
                    continue
                ins, dep = _inside(pp, ob, tol)
                if ins.any():
                    k = tuple(sorted((lb[0], ob[0])))
                    dpx = float(dep.max()) * 16
                    if dpx > hits.get(k, (0, 0))[0]:
                        hits[k] = (dpx, deg)
    return sorted(((a, b, round(v[0], 2), v[1]) for (a, b), v in hits.items()), key=lambda x: -x[2])


# ------------------------------------------------------------------ the audit
def pivots(model):
    out = {}

    def walk(g):
        if g["name"] in ("leaf_l", "leaf_r", "frame") or g["name"].startswith(("gear_", "bolt_", "piston_", "handle_")):
            o = g["origin"]
            out[g["name"]] = (round(-o[0] / 16, 4), round(o[1] / 16, 4), round(-o[2] / 16, 4))
        for c in g["children"]:
            if isinstance(c, dict):
                walk(c)
    for g in model["outliner"]:
        walk(g)
    return out


def _solid(f):
    return not f["el"].startswith("cut_") and "detail" not in f["chain"]


def audit(model, tex, notches=(), ppb=64, verbose=True, dump=None):
    tex = np.asarray(tex)
    rep = {}
    faces_closed = faces_of(model)
    # ---- 1. holes
    solid = [f for f in faces_closed if _solid(f)]
    holes = {}
    for view in ("front", "back"):
        cov = coverage(solid, tex, view, (-2, 0), (2, 6), ppb)
        allowed = np.zeros_like(cov)
        for (X0, X1, Y0, Y1) in notches:
            if view == "front":
                i0, i1 = int(round((X0 * P + 2) * ppb)), int(round((X1 * P + 2) * ppb))
            else:
                i0, i1 = int(round((2 - X1 * P) * ppb)), int(round((2 - X0 * P) * ppb))
            j0, j1 = int(round((6 - Y1 * P) * ppb)), int(round((6 - Y0 * P) * ppb))
            allowed[j0:j1, i0:i1] = True
        # the notches must be open to the top edge (silhouette), never enclosed
        bad = (~cov) & ~(allowed & ~enclosed(cov))
        holes["porte_" + view] = int(bad.sum())
        if dump:
            _dump(cov, bad, os.path.join(dump, "cov_%s.png" % view))
    piv = pivots(model)
    for leaf in ("leaf_l", "leaf_r"):
        lf = [f for f in solid if f["group"] == leaf]
        if not lf:
            continue
        for view in VIEWS:
            if view.startswith("edge"):
                cov = coverage(lf, tex, view, (-0.5, 0), (0.5, 6), ppb)
            else:
                cov = coverage(lf, tex, view, (-2, 0), (2, 6), ppb)
            bad = leaf_holes(cov)
            holes["%s_%s" % (leaf, view)] = int(bad.sum())
            if dump:
                _dump(cov, bad, os.path.join(dump, "cov_%s_%s.png" % (leaf, view)))
    rep["holes"] = holes
    rep["holes_total"] = sum(holes.values())
    # ---- 2. alpha
    rep["alpha"] = alpha_defects(model, tex)
    # ---- 3. coplanar / near faces in every pose, thin cubes
    cop = {}
    for pose, rots in POSES.items():
        fs = faces_closed if not rots else faces_of(model, rots)
        prs = parallel_pairs(fs)
        cop[pose] = [(f["el"], f["fname"], g["el"], g["fname"], round(dd * 16, 4)) for f, g, dd in prs]
    rep["coplanar"] = cop
    rep["coplanar_total"] = sum(len(v) for v in cop.values())
    rep["thin"] = thin_cubes(model)
    # ---- 4. contract
    pts = np.vstack([f["corners"] for f in faces_closed])
    lo, hi = pts.min(0), pts.max(0)
    rep["bounds"] = (lo.round(4).tolist(), hi.round(4).tolist())
    rep["bounds_ok"] = bool(np.all(lo >= BOX_LO - 1e-4) and np.all(hi <= BOX_HI + 1e-4))
    rep["pivots"] = piv
    rep["pivots_ok"] = (abs(piv.get("leaf_l", (9,))[0] + 1.625) < 1e-4 and abs(piv.get("leaf_l", (0, 0, 9))[2]) < 1e-4
                        and abs(piv.get("leaf_r", (9,))[0] - 1.625) < 1e-4 and abs(piv.get("leaf_r", (0, 0, 9))[2]) < 1e-4)
    rep["sweep_back"] = sweep(model, True)
    rep["sweep_front"] = sweep(model, False)
    rep["defects"] = (rep["holes_total"] + len(rep["alpha"]) + rep["coplanar_total"] + len(rep["thin"]) +
                      (0 if rep["bounds_ok"] else 1) + (0 if rep["pivots_ok"] else 1) + len(rep["sweep_back"]))
    if verbose:
        print_report(rep)
    return rep


def print_report(rep):
    print("  AUDIT holes=%d %s" % (rep["holes_total"], {k: v for k, v in rep["holes"].items() if v}))
    print("  AUDIT alpha (solid faces with alpha<255 texels)=%d %s" % (len(rep["alpha"]), rep["alpha"][:6]))
    print("  AUDIT coplanar/near pairs=%d %s" % (rep["coplanar_total"], {k: len(v) for k, v in rep["coplanar"].items()}))
    for pose, v in rep["coplanar"].items():
        for p in v[:8]:
            print("     %s: %s.%s ~ %s.%s  d=%.4fpx" % ((pose,) + p))
    print("  AUDIT thin cubes=%d %s" % (len(rep["thin"]), rep["thin"][:6]))
    print("  AUDIT bounds %s ok=%s ; pivots ok=%s %s" % (rep["bounds"], rep["bounds_ok"], rep["pivots_ok"],
                                                      {k: v for k, v in rep["pivots"].items()}))
    print("  AUDIT sweep backwards (default): %d %s" % (len(rep["sweep_back"]), rep["sweep_back"][:6]))
    print("  AUDIT sweep forwards (option): %d %s" % (len(rep["sweep_front"]), rep["sweep_front"][:4]))
    print("  AUDIT DEFECTS = %d" % rep["defects"])


def _dump(cov, bad, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img = np.zeros(cov.shape + (3,), np.uint8)
    img[cov] = (90, 90, 90)
    img[~cov] = (255, 0, 255)
    img[bad] = (0, 255, 0)
    Image.fromarray(img).save(path)


def load(name):
    with open(os.path.join(ASSETS, "models/entity/%s.bbmodel" % name)) as f:
        model = json.load(f)
    tex = np.array(Image.open(os.path.join(ASSETS, "textures/entity/%s.png" % name)).convert("RGBA"))
    return model, tex


if __name__ == "__main__":
    name = sys.argv[1]
    model, tex = load(name)
    sys.path.insert(0, HERE)
    gen = __import__("generate_" + name)
    scratch = "/tmp/claude-0/-home-user-medieval-ships/2a9b6be4-7c0a-5b40-ad8d-40cfe82b9e67/scratchpad"
    audit(model, tex, getattr(gen, "NOTCHES", ()),
          dump=os.path.join(scratch, "doors_out2/audit_" + name) if "--dump" in sys.argv else None)
