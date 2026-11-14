"""Audit of the three small doors (porte_chene, porte_prison, porte_vapeur), read from the generated files
(src/main/resources/assets/medievalships/models/entity/<id>.bbmodel + textures/entity/<id>.png).

    1. holes      orthographic renders at 64 px per block, background magenta: the closed door seen from the front and
                  from the back must cover the whole opening x [-0.5, 0.5] y [0, 2]; the leaf alone (bone leaf_l) must
                  cover its rectangle seen from the front, the back, both edges, the top and the bottom.
    2. alpha      no drawn face maps a texel whose alpha is < 255 (cut-out sprites must be named *_cutout*).
    3. coplanar   every pair of drawn faces in the same plane (1e-4) that overlap, whatever their directions (the
                  renderer draws both sides), in the poses: closed, closed with the mechanisms moved (bolts out,
                  pistons up, handles and gears turned by 90 degrees), opened backwards by 90 degrees, opened forwards.
    4. sweep      the leaf (and what it carries) turned from 0 to 90 degrees backwards (the default, -z) must not go
                  through any cube of the frame; forwards is reported only.
    5. contract   bones frame / leaf_l (pivot x -0.40625, z 0), everything inside x [-0.5, 0.5] y [0, 2] z [-0.5, 0.5].

Usage: python3 tools/doors/door_audit_small.py [ids...]      (exit status 1 when a defect is found)
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import doorlib_small as ds  # noqa: E402
import preview as pv  # noqa: E402

IDS = ["porte_chene", "porte_prison", "porte_vapeur"]
PPB = 64
EPS_PLANE = 1e-4
MAGENTA = (255, 0, 255)


def load(name):
    with open(os.path.join(ds.ASSETS, "models/entity/%s.bbmodel" % name)) as f:
        model = json.load(f)
    tex = np.array(Image.open(os.path.join(ds.ASSETS, "textures/entity/%s.png" % name)).convert("RGBA")).astype(float)
    return model, tex


def walk(model, fn, groups=None):
    """fn(element, chain) for every element, chain = [its group, parent, ..., root group]."""
    elements = {e["uuid"]: e for e in model["elements"]}

    def rec(g, chain):
        chain = [g] + chain
        for ch in g["children"]:
            if isinstance(ch, dict):
                rec(ch, chain)
            else:
                fn(elements[ch], chain)
    for g in (groups if groups is not None else model["outliner"]):
        rec(g, [])


def find_group(groups, name):
    for g in groups:
        if isinstance(g, dict):
            if g["name"] == name:
                return g
            r = find_group(g["children"], name)
            if r:
                return r
    return None


def to_model(p):
    return np.array([-p[0] / 16, p[1] / 16, -p[2] / 16])


def make_tf(pose):
    """pose: {bone name: (rotation degrees in bb axes, translation in model blocks)} -> transform(point_bb, chain)."""
    def tf(p, chain):
        for g in chain:
            o = np.array(g["origin"], float)
            rot = np.array(g.get("rotation", [0, 0, 0]), float)
            r_add, t = pose.get(g["name"], ((0, 0, 0), (0, 0, 0)))
            R = pv.rot_zyx(rot + np.array(r_add, float))
            tb = np.array([-t[0] * 16, t[1] * 16, -t[2] * 16])
            p = R @ (p - o) + o + tb
        return p
    return tf


def faces(model, pose=None, groups=None):
    """Drawn faces in a pose: dicts (name, part, corners (4 x 3, model blocks), normal, uv)."""
    tf = make_tf(pose or {})
    out = []

    def fn(e, chain):
        f, t = np.array(e["from"], float), np.array(e["to"], float)
        part = next((g["name"] for g in chain if g["name"] == "leaf_l" or g["name"].split("_")[0] in
                     ("gear", "bolt", "piston", "handle")), "frame")
        for fname, face in e["faces"].items():
            if face.get("texture") is None:
                continue
            n, ud, vd = [np.array(x, float) for x in pv.FACES[fname]]
            cs = []
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
                cs.append(to_model(tf(p, chain)))
            cs = np.array(cs)
            nn = np.cross(cs[1] - cs[0], cs[3] - cs[0])
            nn /= max(1e-12, np.linalg.norm(nn))
            out.append(dict(name=e["name"], face=fname, part=part, corners=cs, normal=nn, uv=face["uv"]))
    walk(model, fn, groups)
    return out


def boxes(model, pose=None, groups=None):
    """Cubes in a pose: (name, part, 8 corners in model blocks)."""
    tf = make_tf(pose or {})
    out = []

    def fn(e, chain):
        f, t = np.array(e["from"], float), np.array(e["to"], float)
        part = "leaf" if any(g["name"] == "leaf_l" for g in chain) else "frame"
        cs = np.array([to_model(tf(np.array([(f, t)[a][0], (f, t)[b][1], (f, t)[c][2]]), chain))
                       for a in (0, 1) for b in (0, 1) for c in (0, 1)])
        out.append((e["name"], part, cs))
    walk(model, fn, groups)
    return out


# ---------------------------------------------------------------- 1. holes
def coverage(model, tex, eye, target, groups=None, span=1.25):
    quads = []
    sub = dict(model)
    if groups is not None:
        sub = dict(model, outliner=groups)
    quads = pv.build_mesh(json.loads(json.dumps(sub)), {})
    H = int(round(2 * span * PPB))
    Wd = H
    im, cov = ds.render(quads, [tex], W=Wd, H=H, eye=eye, target=target, ortho=span, bg=MAGENTA, cov=True)
    eye, target = np.array(eye, float), np.array(target, float)
    fwd = target - eye
    fwd /= np.linalg.norm(fwd)
    up = np.array([0, 1, 0.0]) if abs(fwd[1]) < 0.99 else np.array([0, 0, 1.0])
    right = np.cross(fwd, up)
    right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    js, is_ = np.mgrid[0:H, 0:Wd]
    u = (is_ + 0.5 - Wd / 2) / PPB
    v = (H / 2 - (js + 0.5)) / PPB
    P = target[None, None, :] + u[..., None] * right[None, None, :] + v[..., None] * up[None, None, :]
    return im, cov, P


def holes(model, tex, eye, target, rect, groups=None):
    """rect: ((axis, lo, hi), (axis, lo, hi)): pixels whose centre is inside and not covered."""
    span = 1.2
    im, cov, P = coverage(model, tex, eye, target, groups, span)
    inside = np.ones(cov.shape, bool)
    for ax, lo, hi in rect:
        inside &= (P[..., ax] > lo + 1e-9) & (P[..., ax] < hi - 1e-9)
    bad = inside & ~cov
    return int(bad.sum()), int(inside.sum()), im, bad


def leaf_rect(model):
    """The leaf core rectangle (elements core*) in model blocks: x0, x1, y0, y1, z0, z1."""
    lo, hi = np.full(3, 1e9), np.full(3, -1e9)
    for e in model["elements"]:
        if e["name"].startswith(("core", "planks", "plate_")):  # (planks / plate_: the 1.31.0 models)
            for p in (e["from"], e["to"]):
                q = to_model(np.array(p, float))
                lo, hi = np.minimum(lo, q), np.maximum(hi, q)
    return lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]


# ---------------------------------------------------------------- 2. alpha
def transparent(model, tex):
    bad = []
    th, tw = tex.shape[:2]
    sx, sy = tw / model["resolution"]["width"], th / model["resolution"]["height"]
    for e in model["elements"]:
        if "_cutout" in e["name"]:
            continue
        for fname, face in e["faces"].items():
            if face.get("texture") is None:
                continue
            u0, v0, u1, v1 = face["uv"]
            a0, a1 = sorted((u0 * sx, u1 * sx))
            b0, b1 = sorted((v0 * sy, v1 * sy))
            i0, i1 = int(math.floor(a0 + 1e-6)), int(math.ceil(a1 - 1e-6))
            j0, j1 = int(math.floor(b0 + 1e-6)), int(math.ceil(b1 - 1e-6))
            blk = tex[j0:max(j1, j0 + 1), i0:max(i1, i0 + 1), 3]
            n = int((blk < 255).sum())
            if n:
                bad.append((e["name"], fname, n))
    return bad


# ---------------------------------------------------------------- 3. coplanar faces
def coplanar(fs):
    rects = []
    for f in fs:
        n = f["normal"]
        k = int(np.argmax(np.abs(n)))
        if abs(n[k]) < 0.9999:
            continue  # not axis aligned in this pose (never the case in the poses audited)
        o = [j for j in range(3) if j != k]
        c = f["corners"]
        rects.append((k, float(c[:, k].mean()), c[:, o[0]].min(), c[:, o[0]].max(), c[:, o[1]].min(), c[:, o[1]].max(), f))
    buckets = {}
    for r in rects:
        buckets.setdefault((r[0], int(math.floor(r[1] / EPS_PLANE))), []).append(r)
    pairs = []
    seen = set()
    for (k, b), lst in buckets.items():
        cand = lst + buckets.get((k, b + 1), [])
        for i in range(len(lst)):
            ra = lst[i]
            for rb in cand:
                if rb is ra or (id(rb), id(ra)) in seen:
                    continue
                if abs(ra[1] - rb[1]) > EPS_PLANE:
                    continue
                ov1 = min(ra[3], rb[3]) - max(ra[2], rb[2])
                ov2 = min(ra[5], rb[5]) - max(ra[4], rb[4])
                if ov1 > 1e-5 and ov2 > 1e-5:
                    seen.add((id(ra), id(rb)))
                    fa, fb = ra[6], rb[6]
                    pairs.append(("%s/%s" % (fa["name"], fa["face"]), "%s/%s" % (fb["name"], fb["face"]),
                                  "xyz"[k], round(ra[1], 5)))
    return pairs


def mech_pose(model, leaf_deg=0.0, mech=1.0, turn=90.0):
    """Pose with the leaf turned (model degrees about y, + = backwards for leaf_l) and the mechanisms moved."""
    pose = {"leaf_l": ((0, leaf_deg, 0), (0, 0, 0))}
    leaf = find_group(model["outliner"], "leaf_l")
    lx = -leaf["origin"][0] / 16
    middle = lx + abs(lx)   # one leaf spanning the opening: its middle

    def rec(g):
        nm = g["name"]
        if nm.startswith("bolt"):
            sign = -1 if -g["origin"][0] / 16 < middle - 1e-6 else 1
            pose[nm] = ((0, 0, 0), (sign * 0.25 * mech, 0, 0))
        elif nm.startswith("piston"):
            pose[nm] = ((0, 0, 0), (0, 0.25 * mech, 0))
        elif nm.startswith("gear") or nm.startswith("handle"):
            pose[nm] = ((0, 0, turn * mech), (0, 0, 0))
        for ch in g["children"]:
            if isinstance(ch, dict):
                rec(ch)
    for g in model["outliner"]:
        rec(g)
    return pose


# ---------------------------------------------------------------- 4. sweep
def _sat2(a, b):
    """Penetration depth of two convex polygons (xz) or 0."""
    best = 1e9
    for poly in (a, b):
        m = len(poly)
        for i in range(m):
            e = poly[(i + 1) % m] - poly[i]
            nrm = np.array([-e[1], e[0]])
            L = np.linalg.norm(nrm)
            if L < 1e-12:
                continue
            nrm /= L
            pa, pb = a @ nrm, b @ nrm
            ov = min(pa.max(), pb.max()) - max(pa.min(), pb.min())
            if ov <= 0:
                return 0.0
            best = min(best, ov)
    return best


def _poly(cs):
    xz = cs[:, [0, 2]]
    c = xz.mean(axis=0)
    ang = np.arctan2(xz[:, 1] - c[1], xz[:, 0] - c[0])
    pts = xz[np.argsort(ang)]
    keep = [pts[0]]
    for p in pts[1:]:
        if np.linalg.norm(p - keep[-1]) > 1e-9:
            keep.append(p)
    return np.array(keep)


def sweep(model, sign=1, step=2.0):
    """Collisions of the leaf with the frame from 0 to 90 degrees (sign 1 = backwards): {(leaf cube, frame cube): degrees}."""
    hits = {}
    frame = [b for b in boxes(model) if b[1] == "frame"]
    fpolys = [(n, _poly(cs), cs[:, 1].min(), cs[:, 1].max()) for n, _, cs in frame]
    deg = 0.0
    while deg <= 90.0 + 1e-9:
        mech = min(1.0, deg / 18.0)
        pose = mech_pose(model, sign * deg, mech, turn=deg * 4)
        for n, part, cs in boxes(model, pose):
            if part != "leaf":
                continue
            lp, y0, y1 = _poly(cs), cs[:, 1].min(), cs[:, 1].max()
            for fn_, fp, fy0, fy1 in fpolys:
                if min(y1, fy1) - max(y0, fy0) <= 1e-4:
                    continue
                d = _sat2(lp, fp)
                if d > 1e-4:
                    hits.setdefault((n, fn_), []).append(deg)
        deg += step
    return hits


# ---------------------------------------------------------------- 5. contract
def contract(model):
    errs = []
    fr = find_group(model["outliner"], "frame")
    leaf = find_group(model["outliner"], "leaf_l")
    if fr is None:
        errs.append("no frame bone")
    if leaf is None:
        errs.append("no leaf_l bone")
    else:
        o = to_model(np.array(leaf["origin"], float))
        if abs(o[0] - ds.HINGE_X) > 1e-6 or abs(o[2]) > 1e-6:
            errs.append("leaf_l pivot %s" % o)
    for e in model["elements"]:
        for p in (e["from"], e["to"]):
            q = to_model(np.array(p, float))
            if q[0] < -0.5 - 1e-6 or q[0] > 0.5 + 1e-6 or q[1] < -1e-6 or q[1] > 2 + 1e-6 or abs(q[2]) > 0.5 + 1e-6:
                errs.append("%s out of the opening %s" % (e["name"], q))
                break
    bones = []

    def rec(g, depth):
        o = to_model(np.array(g["origin"], float))
        bones.append("%s%s pivot (%.5f, %.5f, %.5f)" % ("  " * depth, g["name"], o[0], o[1], o[2]))
        for ch in g["children"]:
            if isinstance(ch, dict):
                rec(ch, depth + 1)
    for g in model["outliner"]:
        rec(g, 0)
    glows = sorted({e["name"] for e in model["elements"] if e["name"].startswith("glow")})
    return errs, bones, glows


def audit(name, out_dir=None, verbose=True):
    model, tex = load(name)
    res = {}
    # 1. holes
    lx0, lx1, ly0, ly1, lz0, lz1 = leaf_rect(model)
    full = ((0, -0.5, 0.5), (1, 0.0, 2.0))
    leaf = [find_group(model["outliner"], "leaf_l")]
    views = [("porte face", (0, 1, 30), (0, 1, 0), full, None),
             ("porte dos", (0, 1, -30), (0, 1, 0), full, None),
             ("battant face", (0, 1, 30), (0, 1, 0), ((0, lx0, lx1), (1, ly0, ly1)), leaf),
             ("battant dos", (0, 1, -30), (0, 1, 0), ((0, lx0, lx1), (1, ly0, ly1)), leaf),
             ("battant chant +x", (30, 1, 0), (0, 1, 0), ((2, lz0, lz1), (1, ly0, ly1)), leaf),
             ("battant chant -x", (-30, 1, 0), (0, 1, 0), ((2, lz0, lz1), (1, ly0, ly1)), leaf),
             ("battant dessus", (0, 30, 0), (0, 1, 0), ((0, lx0, lx1), (2, lz0, lz1)), leaf),
             ("battant dessous", (0, -30, 0), (0, 1, 0), ((0, lx0, lx1), (2, lz0, lz1)), leaf)]
    res["holes"] = {}
    ims = []
    for title, eye, target, rect, groups in views:
        n, tot, im, bad = holes(model, tex, eye, target, rect, groups)
        res["holes"][title] = n
        a = np.array(im)
        a[bad] = (0, 255, 0)
        ims.append(Image.fromarray(a))
    if out_dir:
        Wt = sum(i.size[0] for i in ims)
        sheet = Image.new("RGB", (Wt, ims[0].size[1]), (0, 0, 0))
        x = 0
        for i in ims:
            sheet.paste(i, (x, 0))
            x += i.size[0]
        os.makedirs(out_dir, exist_ok=True)
        sheet.save(os.path.join(out_dir, "audit_%s.png" % name))
    # 2. alpha
    res["alpha"] = transparent(model, tex)
    # 3. coplanar faces
    poses = {"fermee": {}, "fermee meca": mech_pose(model, 0.0), "ouverte arriere 90": mech_pose(model, 90.0),
             "ouverte avant 90 (info)": mech_pose(model, -90.0)}
    res["coplanar"] = {k: coplanar(faces(model, p)) for k, p in poses.items()}
    # 4. sweep
    res["sweep_back"] = sweep(model, 1)
    res["sweep_front"] = sweep(model, -1)
    # 5. contract
    res["contract"], res["bones"], res["glow"] = contract(model)
    res["defects"] = (sum(res["holes"].values()) + len(res["alpha"]) + sum(len(v) for k, v in res["coplanar"].items()
                      if "info" not in k) + len(res["sweep_back"]) + len(res["contract"]))
    if verbose:
        print("== %s: %d elements" % (name, len(model["elements"])))
        print("  holes:", res["holes"])
        print("  faces with alpha < 255:", len(res["alpha"]), res["alpha"][:8])
        for k, v in res["coplanar"].items():
            print("  coplanar pairs %s: %d" % (k, len(v)), v[:10])
        print("  sweep backwards: %d collisions" % len(res["sweep_back"]),
              {k: (min(v), max(v)) for k, v in list(res["sweep_back"].items())[:10]})
        print("  sweep forwards (info): %d collisions" % len(res["sweep_front"]),
              sorted({k[1] for k in res["sweep_front"]})[:12])
        print("  contract:", res["contract"] or "OK", "| glow:", res["glow"])
        for b in res["bones"]:
            print("   ", b)
        print("  DEFECTS: %d" % res["defects"])
    return res


def main():
    ids = [a for a in sys.argv[1:] if not a.startswith("--")] or IDS
    out = os.path.join(ds.REF_DIR, "..", "doors_out2")
    total = 0
    for name in ids:
        total += audit(name, out)["defects"]
    print("TOTAL DEFECTS: %d" % total)
    sys.exit(1 if total else 0)


if __name__ == "__main__":
    main()
