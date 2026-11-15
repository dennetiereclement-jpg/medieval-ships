#!/usr/bin/env python3
"""Automatic audit of the divine forge models (1.34.0): the structure (forge_divine) and the decor
(forge_divine_deco). Shared by the two model agents; it reads what the game draws (the exported .bbmodel and its
texture) and counts defects (must be ZERO before delivery):

  1. coplanar   pairs of parallel faces (either normal direction: entityCutoutNoCull draws both sides) that
                overlap and lie in the same plane or closer than 1/64 block, in EVERY visibility configuration:
                static + craft_* (or idle_*) + frame k of every flipbook (bones named <family>_f<k>), gears
                (bones gear_*) at 0 and 45 degrees about their local z axis. Faces of two frames of one family
                are never drawn together, so they are never paired.
  2. thin       cubes thinner than 1/64 block (with both faces of that axis drawn).
  3. alpha      faces of solid cubes (name not starting with cut_ / glow_cut_) mapping texels with alpha < 255.
  4. holes      orthographic coverage renders (front, back, 3/4 front-left, 3/4 front-right, 3/4 back) at PPB px per
                block: an uncovered region enclosed by the model is a parasitic hole when it is a pinhole
                (< HOLE_AREA block^2) or a sliver (vanishes under a 1/32-block erosion on each side, i.e. narrower
                than 1/16 block everywhere); wider enclosed openings (pipe arches, gaps between parts) are listed
                (u, v = view-plane coordinates) for review against the reference, not counted.
  5. contract   bounds inside the box, required bones present (structure: fire_f0..3, flow_l_f0..3,
                flow_r_f0..3, gear_a_*, gear_b_*), fx_* bones empty, cubes of fire/flow bones all named glow*.

    python3 tools/forge/forge_audit.py forge_divine [--with forge_divine_deco] [--dump]
    import forge_audit as FA; rep = FA.audit(model, tex)            # in a generator, after export

`--with other` also pairs the faces of the two models against each other (decor vs structure) in every
configuration.
"""
import copy
import json
import math
import os
import re
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, TOOLS)
sys.path.insert(0, os.path.join(TOOLS, "doors"))
import door_audit_large as DA  # noqa: E402
import preview as pv  # noqa: E402

ROOT = os.path.abspath(os.path.join(TOOLS, ".."))
ASSETS = os.path.join(ROOT, "src/main/resources/assets/medievalships")
SCRATCH = "/tmp/claude-0/-home-user-medieval-ships/2a9b6be4-7c0a-5b40-ad8d-40cfe82b9e67/scratchpad"
MIN_GAP = 1.0 / 64
BOX_LO, BOX_HI = np.array([-6.5, 0.0, -3.0]), np.array([6.5, 10.0, 3.0])
HOLE_AREA = 0.004          # block^2: smaller enclosed uncovered regions (pinholes) are parasitic holes
PPB = 64
FRAME_RE = re.compile(r"^(.*)_f(\d+)$")
GEAR_POSES = (0.0, 45.0)


# ------------------------------------------------------------------ bones and configurations
def bone_names(model):
    out = []

    def walk(g):
        out.append(g)
        for c in g["children"]:
            if isinstance(c, dict):
                walk(c)
    for g in model["outliner"]:
        walk(g)
    return out


def families(model):
    fam = {}
    for g in bone_names(model):
        m = FRAME_RE.match(g["name"])
        if m:
            fam.setdefault(m.group(1), set()).add(int(m.group(2)))
    return {k: sorted(v) for k, v in fam.items()}


def gear_bones(model):
    return [g["name"] for g in bone_names(model) if g["name"].startswith("gear_")]


def configurations(model):
    """[(label, frame per family, mode 'craft'/'idle', gear angle)]"""
    fam = families(model)
    nfr = max([len(v) for v in fam.values()] + [1])
    has_idle = any(g["name"].startswith("idle_") for g in bone_names(model))
    out = []
    for ang in GEAR_POSES:
        for k in range(nfr):
            sel = {f: v[k % len(v)] for f, v in fam.items()}
            out.append(("f%d_craft_g%d" % (k, ang), sel, "craft", ang))
            if has_idle:
                out.append(("f%d_idle_g%d" % (k, ang), sel, "idle", ang))
    return out


def visible(chain, sel, mode):
    """Is a face whose bone chain (innermost first) is `chain` drawn in this configuration?"""
    for nm in chain:
        m = FRAME_RE.match(nm)
        if m and m.group(1) in sel and int(m.group(2)) != sel[m.group(1)]:
            return False
        if nm.startswith("craft_") and mode != "craft":
            return False
        if nm.startswith("idle_") and mode != "idle":
            return False
    return True


def posed(model, ang):
    if not ang:
        return model
    rots = {}
    for g in bone_names(model):
        if g["name"].startswith("gear_"):
            r = list(g.get("rotation", [0, 0, 0]))
            r[2] = r[2] + ang
            rots[g["name"]] = r
    return DA.with_rot(model, rots)


def faces_cfg(model, sel, mode, ang, cache):
    key = ang
    if key not in cache:
        cache[key] = DA.faces_of(posed(model, ang))
    return [f for f in cache[key] if visible(f["chain"], sel, mode)]


# ------------------------------------------------------------------ coverage (generic orthographic view)
VIEW_DIRS = {
    "face": (0.0, 0.0, -1.0),
    "dos": (0.0, 0.0, 1.0),
    "3/4_gauche": (0.62, -0.35, -0.70),
    "3/4_droite": (-0.62, -0.35, -0.70),
    "3/4_dos": (0.6, -0.3, 0.74),
}


def view_basis(d):
    d = np.array(d, float)
    d /= np.linalg.norm(d)
    up = np.array([0, 1.0, 0])
    r = np.cross(d, up)
    r /= np.linalg.norm(r)
    u = np.cross(r, d)
    return d, r, u


def coverage(faces, tex, d, ppb=PPB, pad=0.25):
    d, r, u = view_basis(d)
    allc = np.vstack([f["corners"] for f in faces])
    X, Y = allc @ r, allc @ u
    x0, y0 = X.min() - pad, Y.min() - pad
    W = int(math.ceil((X.max() + pad - x0) * ppb))
    H = int(math.ceil((Y.max() + pad - y0) * ppb))
    cov = np.zeros((H, W), bool)
    th, tw = tex.shape[:2]
    for f in faces:
        c = f["corners"]
        U = (c @ r - x0) * ppb
        V = (Y.max() + pad - c @ u) * ppb
        uv = np.array(f["uvs"], float)
        for tri in ((0, 1, 2), (0, 2, 3)):
            ax, ay = U[list(tri)], V[list(tri)]
            det = (ay[1] - ay[2]) * (ax[0] - ax[2]) + (ax[2] - ax[1]) * (ay[0] - ay[2])
            if abs(det) < 1e-9:
                continue
            xa, xb = int(max(0, math.floor(ax.min()))), int(min(W - 1, math.ceil(ax.max())))
            ya, yb = int(max(0, math.floor(ay.min()))), int(min(H - 1, math.ceil(ay.max())))
            if xa > xb or ya > yb:
                continue
            xs, ys = np.meshgrid(np.arange(xa, xb + 1) + 0.5, np.arange(ya, yb + 1) + 0.5)
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
            m &= tex[ty, tx, 3] >= DA.ALPHA_CUT
            cov[ya:yb + 1, xa:xb + 1] |= m
    return cov, (x0, Y.max() + pad, r, u)


def components(mask):
    """4-connected components of a boolean mask: list of arrays of (j, i)."""
    lab = np.zeros(mask.shape, np.int32)
    out = []
    js, is_ = np.nonzero(mask)
    for j, i in zip(js, is_):
        if lab[j, i]:
            continue
        n = len(out) + 1
        stack = [(j, i)]
        lab[j, i] = n
        pts = []
        while stack:
            a, b = stack.pop()
            pts.append((a, b))
            for da, db in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                c, e = a + da, b + db
                if 0 <= c < mask.shape[0] and 0 <= e < mask.shape[1] and mask[c, e] and not lab[c, e]:
                    lab[c, e] = n
                    stack.append((c, e))
        out.append(np.array(pts))
    return out


def erode(mask, k):
    m = mask.copy()
    for _ in range(k):
        n = m.copy()
        n[1:, :] &= m[:-1, :]
        n[:-1, :] &= m[1:, :]
        n[:, 1:] &= m[:, :-1]
        n[:, :-1] &= m[:, 1:]
        n[0, :] = n[-1, :] = n[:, 0] = n[:, -1] = False
        m = n
    return m


def holes(faces, tex, ppb=PPB, dump=None):
    out, openings = {}, {}
    where = {}
    k = max(1, int(round(ppb / 32)))       # erosion of 1/32 block on each side: gaps under 1/16 block vanish
    for view, d in VIEW_DIRS.items():
        cov, frame = coverage(faces, tex, d, ppb)
        enc = DA.enclosed(cov)
        thick = erode(enc, k)
        bad = np.zeros_like(enc)
        ops = []
        for comp in components(enc):
            area = len(comp) / ppb ** 2
            sub = thick[comp[:, 0], comp[:, 1]]
            j, i = comp.mean(0)
            loc = (round(area, 4), round(float(frame[0] + i / ppb), 2), round(float(frame[1] - j / ppb), 2))
            if area < HOLE_AREA or not sub.any():
                bad[comp[:, 0], comp[:, 1]] = True
                where.setdefault(view, []).append(loc)
            else:
                ops.append(loc)
        out[view] = int(bad.sum())
        openings[view] = ops
        if where.get(view):
            print("     parasitic holes %s (area, u, v): %s" % (view, where[view][:10]))
        if dump:
            os.makedirs(dump, exist_ok=True)
            img = np.zeros(cov.shape + (3,), np.uint8)
            img[cov] = (90, 90, 90)
            img[~cov] = (255, 0, 255)
            img[enc] = (0, 0, 255)
            img[bad] = (0, 255, 0)
            Image.fromarray(img).save(os.path.join(dump, "cov_%s.png" % view.replace("/", "-")))
    return out, openings


# ------------------------------------------------------------------ contract
def contract(model, structure=True):
    probs = []
    names = {g["name"]: g for g in bone_names(model)}
    elements = {e["uuid"]: e for e in model["elements"]}
    if structure:
        need = ["fire_f%d" % k for k in range(4)] + ["flow_l_f%d" % k for k in range(4)] + \
               ["flow_r_f%d" % k for k in range(4)]
        for n in need:
            if n not in names:
                probs.append("bone missing: " + n)
        if not any(n.startswith("gear_a_") for n in names) or not any(n.startswith("gear_b_") for n in names):
            probs.append("gear_a_* / gear_b_* missing")
        if not any(n.startswith("craft_") for n in names):
            probs.append("no craft_* bone")
    for n, g in names.items():
        if n.startswith("fx_") and any(not isinstance(c, dict) for c in g["children"]):
            probs.append("fx bone with cubes: " + n)
        if FRAME_RE.match(n) and (n.startswith("fire_") or n.startswith("flow_")):
            def walk(gr):
                for c in gr["children"]:
                    if isinstance(c, dict):
                        walk(c)
                    elif not elements[c]["name"].startswith("glow"):
                        probs.append("non-glow cube in %s: %s" % (n, elements[c]["name"]))
            walk(g)
    return probs


# ------------------------------------------------------------------ the audit
def audit(model, tex, other=None, verbose=True, dump=None, structure=True, ppb=PPB):
    tex = np.asarray(tex)
    rep = {}
    cache = {}
    cfgs = configurations(model)
    cop = {}
    for label, sel, mode, ang in cfgs:
        fs = faces_cfg(model, sel, mode, ang, cache)
        prs = DA.parallel_pairs(fs)
        cop[label] = [(f["el"], f["fname"], g["el"], g["fname"], round(dd * 16, 4)) for f, g, dd in prs]
    rep["coplanar"] = cop
    rep["coplanar_total"] = sum(len(v) for v in cop.values())
    cross = {}
    if other is not None:
        om, ot = other
        ocache = {}
        for label, sel, mode, ang in cfgs:
            fa = faces_cfg(model, sel, mode, ang, cache)
            ocfg = configurations(om)
            o = next((c for c in ocfg if c[3] == ang), ocfg[0])
            fb = faces_cfg(om, o[1], o[2], o[3], ocache)
            for f in fb:
                f["uuid"] = "other:" + f["uuid"]
            prs = [p for p in DA.parallel_pairs(fa + fb) if (p[0]["uuid"].startswith("other:")) != (p[1]["uuid"].startswith("other:"))]
            for f in fb:
                f["uuid"] = f["uuid"][6:]
            cross[label] = [(f["el"], f["fname"], g["el"], g["fname"], round(dd * 16, 4)) for f, g, dd in prs]
    rep["cross"] = cross
    rep["cross_total"] = sum(len(v) for v in cross.values())
    rep["thin"] = DA.thin_cubes(model)
    rep["alpha"] = DA.alpha_defects(model, tex)
    # holes: the static model + frame 0 + craft (what is always drawn plus the densest state), no detail bones
    lab, sel, mode, ang = cfgs[0]
    fs = [f for f in faces_cfg(model, sel, mode, ang, cache) if not DA.is_cut(f["el"]) and "detail" not in f["chain"]]
    h, ops = holes(fs, tex, ppb, dump)
    rep["holes"], rep["openings"] = h, ops
    rep["holes_total"] = sum(h.values())
    allf = cache[0.0] if 0.0 in cache else DA.faces_of(model)
    pts = np.vstack([f["corners"] for f in allf])
    lo, hi = pts.min(0), pts.max(0)
    rep["bounds"] = (lo.round(3).tolist(), hi.round(3).tolist())
    rep["bounds_ok"] = bool(np.all(lo >= BOX_LO - 1e-4) and np.all(hi <= BOX_HI + 1e-4))
    rep["contract"] = contract(model, structure)
    rep["cubes"] = len(model["elements"])
    rep["defects"] = (rep["coplanar_total"] + rep["cross_total"] + len(rep["thin"]) + len(rep["alpha"]) +
                      rep["holes_total"] + (0 if rep["bounds_ok"] else 1) + len(rep["contract"]))
    if verbose:
        print_report(rep)
    return rep


def print_report(rep):
    print("  AUDIT cubes=%d, configurations=%d" % (rep["cubes"], len(rep["coplanar"])))
    print("  AUDIT coplanar/near pairs=%d %s" % (rep["coplanar_total"], {k: len(v) for k, v in rep["coplanar"].items() if v}))
    seen = set()
    for cfg, v in rep["coplanar"].items():
        for p in v:
            if p[:4] in seen:
                continue
            seen.add(p[:4])
            if len(seen) <= 25:
                print("     %s: %s.%s ~ %s.%s d=%.4fpx" % ((cfg,) + p))
    if rep["cross"]:
        print("  AUDIT cross pairs (with the other model)=%d" % rep["cross_total"])
        for cfg, v in rep["cross"].items():
            for p in v[:10]:
                print("     %s: %s.%s ~ %s.%s d=%.4fpx" % ((cfg,) + p))
    print("  AUDIT thin cubes=%d %s" % (len(rep["thin"]), rep["thin"][:6]))
    print("  AUDIT alpha (solid faces with alpha<255 texels)=%d %s" % (len(rep["alpha"]), rep["alpha"][:6]))
    print("  AUDIT holes=%d %s" % (rep["holes_total"], rep["holes"]))
    for v, ops in rep["openings"].items():
        if ops:
            print("     openings %s (area, x, y): %s" % (v, ops[:8]))
    print("  AUDIT bounds %s ok=%s" % (rep["bounds"], rep["bounds_ok"]))
    print("  AUDIT contract problems=%d %s" % (len(rep["contract"]), rep["contract"][:8]))
    print("  AUDIT DEFECTS = %d" % rep["defects"])


def load(name):
    with open(os.path.join(ASSETS, "models/entity/%s.bbmodel" % name)) as f:
        model = json.load(f)
    tex = np.array(Image.open(os.path.join(ASSETS, "textures/entity/%s.png" % name)).convert("RGBA"))
    return model, tex


if __name__ == "__main__":
    name = sys.argv[1]
    model, tex = load(name)
    other = None
    if "--with" in sys.argv:
        other = load(sys.argv[sys.argv.index("--with") + 1])
    audit(model, tex, other, structure=(name == "forge_divine"),
          dump=os.path.join(SCRATCH, "forge_out/audit_" + name) if "--dump" in sys.argv else None)
