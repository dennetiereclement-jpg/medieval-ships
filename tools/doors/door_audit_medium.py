#!/usr/bin/env python3
"""Automatic audit of the four MEDIUM doors (1.32.0): porte_grange, porte_forteresse, porte_industrielle,
porte_marchande. Reads the exported models (models/entity/<id>.bbmodel + textures/entity/<id>.png), the way the
game draws them (BbModel + MeshEmitter: a face is skipped when seen from behind only if its cube has the opposite
face; texels with alpha < 0.1 are cut out), and counts:

  holes      background pixels inside the opening rectangle, door closed, orthographic front and back (64 px per
             block, twice with a half pixel shift); each leaf alone: background inside its own outline (front, back,
             both edges, four oblique views of the open leaf) - an enclosed background region is a hole, and seen on
             edge every pixel row must be one solid run (no daylight between the battens and the core)
  alpha      faces that map texels whose alpha is below 255
  coplanar   pairs of faces in the same plane (1e-4 block) that overlap, any direction, door closed and open 90
             degrees; `near` = parallel overlapping faces closer than 1/64 block (not in the same plane)
  sweep      interpenetration of the leaves with the frame and with each other while both turn 0 -> 90 degrees
             towards the back (and the same towards the front, only reported)
  contract   bounds x [-1, 1], y [0, 4], z [-0.5, 0.5] closed; pivots of leaf_l / leaf_r; bone names

    python3 tools/doors/door_audit_medium.py [id ...] [--verbose]
"""
import json
import math
import os
import sys
from collections import defaultdict

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../.."))
ASSETS = os.path.join(ROOT, "src/main/resources/assets/medievalships")
IDS = ["porte_grange", "porte_forteresse", "porte_industrielle", "porte_marchande"]

FACES = {  # normal, u dir, v dir (bb space), same table as tools/preview.py and BbModel
    "north": ((0, 0, -1), (-1, 0, 0), (0, -1, 0)),
    "south": ((0, 0, 1), (1, 0, 0), (0, -1, 0)),
    "west": ((-1, 0, 0), (0, 0, 1), (0, -1, 0)),
    "east": ((1, 0, 0), (0, 0, -1), (0, -1, 0)),
    "up": ((0, 1, 0), (1, 0, 0), (0, 0, 1)),
    "down": ((0, -1, 0), (1, 0, 0), (0, 0, -1)),
}
OPP = {"north": "south", "south": "north", "west": "east", "east": "west", "up": "down", "down": "up"}


def rot_zyx(deg):
    a, b, c = [math.radians(d) for d in deg]
    ca, sa, cb, sb, cc, sc = math.cos(a), math.sin(a), math.cos(b), math.sin(b), math.cos(c), math.sin(c)
    Rx = np.array([[1, 0, 0], [0, ca, -sa], [0, sa, ca]])
    Ry = np.array([[cb, 0, sb], [0, 1, 0], [-sb, 0, cb]])
    Rz = np.array([[cc, -sc, 0], [sc, cc, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


def load(door_id):
    src = os.environ.get("DOOR_AUDIT_DIR")   # a folder holding <id>.bbmodel and <id>.png (e.g. a saved older version)
    mp = os.path.join(src, door_id + ".bbmodel") if src else os.path.join(ASSETS, "models/entity/%s.bbmodel" % door_id)
    tp = os.path.join(src, door_id + ".png") if src else os.path.join(ASSETS, "textures/entity/%s.png" % door_id)
    with open(mp) as f:
        model = json.load(f)
    tex = np.array(Image.open(tp).convert("RGBA")).astype(float)
    return model, tex


# ---------------------------------------------------------------- geometry
def bones_of(model):
    """name -> (origin bb, rotation, parent name); element uuid -> bone chain (innermost first)."""
    info, chain_of = {}, {}

    def walk(g, chain):
        chain = [g] + chain
        info[g["name"]] = g
        for ch in g["children"]:
            if isinstance(ch, dict):
                walk(ch, chain)
            else:
                chain_of[ch] = chain
    for g in model["outliner"]:
        walk(g, [])
    return info, chain_of


def to_model(p):
    return np.array([-p[0] / 16, p[1] / 16, -p[2] / 16])


def element_frames(model, angle=0.0, only=None):
    """Per element: (element, bone names of the chain, function bb point -> model point in blocks)."""
    _, chain_of = bones_of(model)
    out = []
    for e in model["elements"]:
        chain = chain_of[e["uuid"]]
        names = [g["name"] for g in chain]
        if only is not None and not (set(names) & set(only)):
            continue
        mats = []
        for g in chain:
            rot = list(g.get("rotation", [0, 0, 0]))
            if g["name"] == "leaf_l":
                rot = [rot[0], rot[1] + angle, rot[2]]
            elif g["name"] == "leaf_r":
                rot = [rot[0], rot[1] - angle, rot[2]]
            mats.append((np.array(g["origin"], float), rot_zyx(rot)))
        eo = np.array(e.get("origin", [0, 0, 0]), float)
        eR = rot_zyx(e.get("rotation", [0, 0, 0]))

        def tf(p, mats=mats, eo=eo, eR=eR):
            p = eR @ (np.asarray(p, float) - eo) + eo
            for o, R in mats:
                p = R @ (p - o) + o
            return to_model(p)
        out.append((e, names, tf))
    return out


def faces(model, angle=0.0, only=None):
    """Every textured face: corners (4 x 3, model blocks), uvs, glow, two-sided, outward normal, names."""
    out = []
    for e, names, tf in element_frames(model, angle, only):
        f, t = np.array(e["from"], float), np.array(e["to"], float)
        glow = e["name"].startswith("glow")
        for fname, face in e["faces"].items():
            if face.get("texture") is None:
                continue
            n, ud, vd = [np.array(x, float) for x in FACES[fname]]
            corners, uvs = [], []
            u1, v1, u2, v2 = face["uv"]
            for cu, cv in ((0, 0), (1, 0), (1, 1), (0, 1)):
                p = np.empty(3)
                for ax in range(3):
                    if n[ax] != 0:
                        p[ax] = t[ax] if n[ax] > 0 else f[ax]
                    elif ud[ax] != 0:
                        lo, hi = (f[ax], t[ax]) if ud[ax] > 0 else (t[ax], f[ax])
                        p[ax] = lo + (hi - lo) * cu
                    else:
                        lo, hi = (f[ax], t[ax]) if vd[ax] > 0 else (t[ax], f[ax])
                        p[ax] = lo + (hi - lo) * cv
                corners.append(tf(p))
                uvs.append((u1 + (u2 - u1) * cu, v1 + (v2 - v1) * cv))
            corners = np.array(corners)
            # outward normal in model space: transform two points
            c0 = np.array([(f[k] + t[k]) / 2 for k in range(3)])
            nrm = tf(c0 + n) - tf(c0)
            nrm /= np.linalg.norm(nrm)
            opp = e["faces"].get(OPP[fname])
            two = opp is None or opp.get("texture") is None
            out.append(dict(c=corners, uv=uvs, glow=glow, two=two, n=nrm, el=e["name"], face=fname, bones=names,
                            uuid=e["uuid"], tex=face.get("texture")))
    return out


# ---------------------------------------------------------------- rasteriser (coverage)
def render(fl, tex, W, H, eye, target, ortho=None, fov=None, shift=(0.0, 0.0), cull=True):
    eye, target = np.array(eye, float), np.array(target, float)
    fwd = target - eye
    fwd /= np.linalg.norm(fwd)
    up = np.array([0, 1, 0.0]) if abs(fwd[1]) < 0.99 else np.array([0, 0, 1.0])
    right = np.cross(fwd, up)
    right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    img = np.zeros((H, W, 3), float)
    cov = np.zeros((H, W), bool)
    zbuf = np.full((H, W), np.inf)
    th_, tw_ = tex.shape[0], tex.shape[1]

    def project(p):
        d = p - eye
        x, y, z = d @ right, d @ up, d @ fwd
        if ortho:
            s = W / ortho
            return np.array([W / 2 + x * s + shift[0], H / 2 - y * s + shift[1], z])
        f = (H / 2) / math.tan(math.radians(fov) / 2)
        return np.array([W / 2 + x * f / z, H / 2 - y * f / z, z])

    for q in fl:
        if cull and not q["two"]:
            view = fwd if ortho else q["c"][0] - eye
            if np.dot(q["n"], view) > 0:
                continue
        P = [project(c) for c in q["c"]]
        sh = 1.0 if q["glow"] else q["n"][0] ** 2 * 0.6 + q["n"][2] ** 2 * 0.8 + q["n"][1] ** 2 * (1.0 if q["n"][1] > 0 else 0.5)
        for tri in ((0, 1, 2), (0, 2, 3)):
            a, b, c = (P[i] for i in tri)
            if min(a[2], b[2], c[2]) <= 0.05:
                continue
            ua, ub, uc = (np.array(q["uv"][i]) for i in tri)
            xmin, xmax = int(max(0, math.floor(min(a[0], b[0], c[0])))), int(min(W - 1, math.ceil(max(a[0], b[0], c[0]))))
            ymin, ymax = int(max(0, math.floor(min(a[1], b[1], c[1])))), int(min(H - 1, math.ceil(max(a[1], b[1], c[1]))))
            if xmin > xmax or ymin > ymax:
                continue
            xs, ys = np.meshgrid(np.arange(xmin, xmax + 1) + 0.5, np.arange(ymin, ymax + 1) + 0.5)
            det = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
            if abs(det) < 1e-12:
                continue
            w0 = ((b[1] - c[1]) * (xs - c[0]) + (c[0] - b[0]) * (ys - c[1])) / det
            w1 = ((c[1] - a[1]) * (xs - c[0]) + (a[0] - c[0]) * (ys - c[1])) / det
            w2 = 1 - w0 - w1
            m = (w0 >= -1e-9) & (w1 >= -1e-9) & (w2 >= -1e-9)
            if not m.any():
                continue
            if ortho:
                z = w0 * a[2] + w1 * b[2] + w2 * c[2]
                uu = w0 * ua[0] + w1 * ub[0] + w2 * uc[0]
                vv = w0 * ua[1] + w1 * ub[1] + w2 * uc[1]
            else:
                iz = w0 / a[2] + w1 / b[2] + w2 / c[2]
                z = 1 / iz
                uu = (w0 * ua[0] / a[2] + w1 * ub[0] / b[2] + w2 * uc[0] / c[2]) * z
                vv = (w0 * ua[1] / a[2] + w1 * ub[1] / b[2] + w2 * uc[1] / c[2]) * z
            tx = np.clip(np.floor(uu).astype(int), 0, tw_ - 1)
            ty = np.clip(np.floor(vv).astype(int), 0, th_ - 1)
            col = tex[ty, tx]
            m &= col[..., 3] >= 26
            sub = zbuf[ymin:ymax + 1, xmin:xmax + 1]
            m &= z < sub - 1e-7
            if not m.any():
                continue
            sub[m] = z[m]
            img[ymin:ymax + 1, xmin:xmax + 1][m] = col[..., :3][m] * sh
            cov[ymin:ymax + 1, xmin:xmax + 1][m] = True
    return img, cov


def enclosed(cov):
    """Background pixels not connected (4-neighbours) to the image border: holes."""
    H, W = cov.shape
    seen = np.zeros_like(cov)
    stack = [(j, i) for j in range(H) for i in (0, W - 1) if not cov[j, i]] + \
            [(j, i) for i in range(W) for j in (0, H - 1) if not cov[j, i]]
    for j, i in stack:
        seen[j, i] = True
    while stack:
        j, i = stack.pop()
        for dj, di in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            a, b = j + dj, i + di
            if 0 <= a < H and 0 <= b < W and not cov[a, b] and not seen[a, b]:
                seen[a, b] = True
                stack.append((a, b))
    return (~cov) & (~seen)


# ---------------------------------------------------------------- checks
PPB = 64
DUMP = None   # directory: images of the views with defects (holes in red)


def _dump(door_id, view, cov, bad):
    if DUMP is None or not bad.any():
        return
    im = np.zeros(cov.shape + (3,), np.uint8)
    im[cov] = (90, 90, 90)
    im[bad] = (255, 0, 0)
    os.makedirs(DUMP, exist_ok=True)
    Image.fromarray(im).save(os.path.join(DUMP, "%s_%s.png" % (door_id, view)))


def check_holes(model, tex, verbose=False, door_id="door"):
    res = {}
    fl = faces(model, 0.0)
    W, H = 2 * PPB, 4 * PPB
    for name, eye in (("front", (0, 2, 40)), ("back", (0, 2, -40))):
        n = 0
        for sh in ((0, 0), (0.5, 0.5)):
            _, cov = render(fl, tex, W, H, eye, (0, 2, 0), ortho=2.0, shift=sh)
            n += int((~cov).sum())
            _dump(door_id, "closed_" + name, cov, ~cov)
        res["closed_" + name] = n
    # oblique views of the closed door: enclosed background
    for k, eye in enumerate(((-2.5, 2.6, 4.5), (2.5, 1.4, 4.5), (-2.5, 2.6, -4.5), (2.5, 1.4, -4.5))):
        _, cov = render(fl, tex, 260, 360, eye, (0, 2, 0), fov=60)
        res["closed_oblique_%d" % k] = int(enclosed(cov).sum())
        _dump(door_id, "closed_oblique_%d" % k, cov, enclosed(cov))
    # each leaf alone
    for leaf, hx in (("leaf_l", -0.75), ("leaf_r", 0.75)):
        lf = faces(model, 0.0, only=[leaf])
        # outline of the core boxes (front projection), the rest is relief
        cores = [e for e, names, tf in element_frames(model, 0.0, only=[leaf]) if e["name"].startswith("core")]
        mask = np.zeros((H, W), bool)
        for e in cores:
            x0, x1 = sorted((-e["from"][0] / 16, -e["to"][0] / 16))
            y0, y1 = sorted((e["from"][1] / 16, e["to"][1] / 16))
            i0, i1 = int(math.ceil((x0 + 1) * PPB - 1e-6)), int(math.floor((x1 + 1) * PPB + 1e-6))
            j0, j1 = int(math.ceil((4 - y1) * PPB - 1e-6)), int(math.floor((4 - y0) * PPB + 1e-6))
            mask[j0:j1, i0:i1] = True
        for name, eye in (("front", (0, 2, 40)), ("back", (0, 2, -40))):
            n = 0
            for sh in ((0, 0), (0.5, 0.5)):
                _, cov = render(lf, tex, W, H, eye, (0, 2, 0), ortho=2.0, shift=sh)
                mk = mask if name == "front" else mask[:, ::-1]
                n += int((mk & ~cov).sum()) + int(enclosed(cov).sum())
                _dump(door_id, "%s_%s" % (leaf, name), cov, mk & ~cov | enclosed(cov))
            res["%s_%s" % (leaf, name)] = n
        # on edge: looking along x (both ways), 64 px per block over z [-0.5, 0.5]; the moving parts hung on the
        # leaf (handle_*, gear_*, bolt_*: they need their clearance) are left out
        body = [f for f in lf if not f["bones"][0].startswith(("handle_", "gear_", "bolt_", "piston_"))]
        for name, eye in (("edge+x", (40, 2, 0)), ("edge-x", (-40, 2, 0))):
            _, cov = render(body, tex, PPB, H, eye, (0, 2, 0), ortho=1.0)
            holes = enclosed(cov)
            for j in range(H):
                idx = np.nonzero(cov[j])[0]
                if len(idx):
                    holes[j, idx[0]:idx[-1] + 1] |= ~cov[j, idx[0]:idx[-1] + 1]
            res["%s_%s" % (leaf, name)] = int(holes.sum())
            _dump(door_id, "%s_%s" % (leaf, name), cov, holes)
        # open 90 degrees, oblique views from both sides of the leaf
        of = faces(model, 90.0, only=[leaf])
        c = np.array([hx, 2.0, -0.4])
        for k, d in enumerate(((1.0, 0.35, 0.8), (1.0, -0.2, -0.9), (-1.0, 0.3, 0.7), (-1.0, -0.25, -0.8))):
            d = np.array(d) if hx < 0 else np.array(d) * np.array([-1, 1, 1])
            eye = c + 4.0 * d / np.linalg.norm(d)
            _, cov = render(of, tex, 300, 420, eye, c, fov=65)
            res["%s_open_%d" % (leaf, k)] = int(enclosed(cov).sum())
            _dump(door_id, "%s_open_%d" % (leaf, k), cov, enclosed(cov))
    return res


def check_alpha(model, tex):
    bad = []
    for e in model["elements"]:
        for fname, face in e["faces"].items():
            if face.get("texture") is None:
                continue
            u1, v1, u2, v2 = face["uv"]
            x0, x1 = sorted((u1, u2))
            y0, y1 = sorted((v1, v2))
            i0, i1 = int(math.floor(x0 + 1e-6)), int(math.ceil(x1 - 1e-6))
            j0, j1 = int(math.floor(y0 + 1e-6)), int(math.ceil(y1 - 1e-6))
            if i1 <= i0 or j1 <= j0:
                continue
            a = tex[j0:j1, i0:i1, 3]
            if (a < 255).any():
                bad.append((e["name"], fname, int((a < 255).sum())))
    return bad


def _basis(n):
    a = np.array([1.0, 0, 0]) if abs(n[0]) < 0.9 else np.array([0, 1.0, 0])
    u = np.cross(n, a)
    u /= np.linalg.norm(u)
    return u, np.cross(n, u)


def _overlap2d(P, Q, tol):
    """Convex polygons (k x 2) overlap by more than tol on every separating axis?"""
    for poly in (P, Q):
        k = len(poly)
        for i in range(k):
            e = poly[(i + 1) % k] - poly[i]
            L = np.linalg.norm(e)
            if L < 1e-12:
                continue
            ax = np.array([-e[1], e[0]]) / L
            pp, qq = P @ ax, Q @ ax
            if min(pp.max(), qq.max()) - max(pp.min(), qq.min()) <= tol:
                return False
    return True


def check_coplanar(model, angle, tol=1e-4, near=1 / 64.0):
    fl = faces(model, angle)
    buckets = defaultdict(list)
    for i, f in enumerate(fl):
        n = f["n"]
        sgn = 1
        for x in n:
            if abs(x) > 1e-3:
                sgn = 1 if x > 0 else -1
                break
        f["cn"] = n * sgn
        f["d"] = float(np.dot(f["cn"], f["c"][0]))
        buckets[tuple(np.round(f["cn"] * 50).astype(int))].append(i)
    pairs, nears = [], []
    for idx in buckets.values():
        idx.sort(key=lambda i: fl[i]["d"])
        for a in range(len(idx)):
            f = fl[idx[a]]
            u, v = _basis(f["cn"])
            P = np.array([[c @ u, c @ v] for c in f["c"]])
            for b in range(a + 1, len(idx)):
                g = fl[idx[b]]
                dd = g["d"] - f["d"]
                if dd > near:
                    break
                if g["uuid"] == f["uuid"]:
                    continue
                if abs(np.dot(f["cn"], g["cn"])) < 0.99999:
                    continue
                Q = np.array([[c @ u, c @ v] for c in g["c"]])
                if tol < dd < near - 1e-7 or dd <= tol:
                    pass
                else:
                    continue
                if not _overlap2d(P, Q, 1e-4):
                    continue
                rec = (f["el"], f["face"], f["bones"][0], g["el"], g["face"], g["bones"][0],
                       "same" if np.dot(f["n"], g["n"]) > 0 else "opposite", round(dd * 16, 4))
                (pairs if dd <= tol else nears).append(rec)
    return pairs, nears


# -- oriented boxes (sweep)
def obbs(model, angle, only):
    out = []
    for e, names, tf in element_frames(model, angle, only):
        f, t = np.array(e["from"], float), np.array(e["to"], float)
        c = tf((f + t) / 2)
        axes, half = [], []
        for k in range(3):
            d = np.zeros(3)
            d[k] = (t[k] - f[k]) / 2
            v = tf((f + t) / 2 + d) - c
            L = np.linalg.norm(v)
            half.append(L)
            axes.append(v / L if L > 1e-12 else np.eye(3)[k])
        out.append((e["name"], c, np.array(axes), np.array(half)))
    return out


def penetration(A, B):
    """Overlap depth of two oriented boxes (separating axis theorem), <= 0 when apart."""
    _, ca, Aa, ha = A
    _, cb, Ab, hb = B
    axes = list(Aa) + list(Ab)
    for i in range(3):
        for j in range(3):
            c = np.cross(Aa[i], Ab[j])
            L = np.linalg.norm(c)
            if L > 1e-6:
                axes.append(c / L)
    d = cb - ca
    best = 1e9
    for ax in axes:
        ra = sum(ha[k] * abs(np.dot(Aa[k], ax)) for k in range(3))
        rb = sum(hb[k] * abs(np.dot(Ab[k], ax)) for k in range(3))
        o = ra + rb - abs(np.dot(d, ax))
        if o < best:
            best = o
            if best <= 0:
                return best
    return best


def check_sweep(model, sign=1.0, step=3.0):
    worst = (0.0, None)
    frame = obbs(model, 0.0, ["frame"])
    for a in np.arange(step, 90.0 + 1e-6, step):
        L = obbs(model, sign * a, ["leaf_l"])
        R = obbs(model, sign * a, ["leaf_r"])
        for grp, others in ((L, frame), (R, frame), (L, R)):
            for A in grp:
                for B in others:
                    if np.linalg.norm(A[1] - B[1]) > np.linalg.norm(A[3]) + np.linalg.norm(B[3]):
                        continue
                    p = penetration(A, B)
                    if p > worst[0]:
                        worst = (p, (round(float(a), 1), A[0], B[0]))
    return worst


def check_contract(model):
    errs = []
    info, _ = bones_of(model)
    for need in ("frame", "leaf_l", "leaf_r"):
        if need not in info:
            errs.append("missing bone " + need)
    for name, x in (("leaf_l", -0.75), ("leaf_r", 0.75)):
        if name in info:
            o = info[name]["origin"]
            if abs(-o[0] / 16 - x) > 1e-4 or abs(o[2]) > 1e-4:
                errs.append("%s pivot %s" % (name, o))
    lo, hi = np.full(3, 1e9), np.full(3, -1e9)
    for f in faces(model, 0.0):
        lo, hi = np.minimum(lo, f["c"].min(0)), np.maximum(hi, f["c"].max(0))
    if lo[0] < -1 - 1e-4 or hi[0] > 1 + 1e-4 or lo[1] < -1e-4 or hi[1] > 4 + 1e-4 or lo[2] < -0.5 - 1e-4 or hi[2] > 0.5 + 1e-4:
        errs.append("bounds %s %s" % (np.round(lo, 4), np.round(hi, 4)))
    names = sorted(info)
    return errs, names, (np.round(lo, 4).tolist(), np.round(hi, 4).tolist())


def audit(door_id, verbose=False):
    model, tex = load(door_id)
    holes = check_holes(model, tex, verbose, door_id)
    alpha = check_alpha(model, tex)
    cp0, near0 = check_coplanar(model, 0.0)
    cp90, near90 = check_coplanar(model, 90.0)
    sweep_back = check_sweep(model, 1.0)
    sweep_front = check_sweep(model, -1.0)
    errs, names, bounds = check_contract(model)
    n_holes = sum(holes.values())
    print("== %s: %d cubes" % (door_id, len(model["elements"])))
    print("  holes %d  %s" % (n_holes, {k: v for k, v in holes.items() if v} or "none"))
    print("  alpha<255 faces %d %s" % (len(alpha), alpha[:8] if verbose else alpha[:3]))
    print("  coplanar closed %d (near %d), open90 %d (near %d)" % (len(cp0), len(near0), len(cp90), len(near90)))
    for p in (cp0 + near0)[: (40 if verbose else 6)]:
        print("    closed", p)
    for p in (cp90 + near90)[: (40 if verbose else 6)]:
        print("    open90", p)
    print("  sweep back: max penetration %.3f px %s" % (sweep_back[0] * 16, sweep_back[1]))
    print("  sweep front (info): max penetration %.3f px %s" % (sweep_front[0] * 16, sweep_front[1]))
    print("  contract %s bounds %s" % (errs or "OK", bounds))
    print("  bones %s" % names)
    return dict(holes=n_holes, holes_detail=holes, alpha=len(alpha), coplanar=len(cp0) + len(cp90),
                near=len(near0) + len(near90), sweep=sweep_back[0] * 16, sweep_front=sweep_front[0] * 16,
                contract=errs)


if __name__ == "__main__":
    ids = [a for a in sys.argv[1:] if not a.startswith("--")] or IDS
    for a in sys.argv[1:]:
        if a.startswith("--dump="):
            DUMP = a[7:]
    tot = {}
    for i in ids:
        tot[i] = audit(i, "--verbose" in sys.argv)
    print()
    for i, r in tot.items():
        print("%-20s holes %5d  alpha %3d  coplanar %4d  near %4d  sweep %.3f px  front %.3f px  contract %s" % (
            i, r["holes"], r["alpha"], r["coplanar"], r["near"], r["sweep"], r["sweep_front"], "OK" if not r["contract"] else r["contract"]))
