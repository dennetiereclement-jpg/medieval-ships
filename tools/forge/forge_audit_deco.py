"""Audit du modele DECOR de la Forge divine (et du decor CONTRE la structure de l'agent A).

    python3 tools/forge/forge_audit_deco.py [--with forge_divine] [--sheet out.png]

1. coplanar   toute paire de faces dessinees paralleles (normales egales OU opposees, plans quelconques, pas seulement
              alignes) a moins de 1/64 bloc l'une de l'autre et qui se recouvrent (polygones projetes, SAT) ; tous les
              os visibles (craft_* compris : c'est l'etat le plus charge). Avec --with : paires decor/structure.
2. thin       cube d'epaisseur < 1/64 bloc.
3. alpha      face dessinee qui lit un texel alpha < 255 (seuls cut_* / glow_cut_* exemptes).
4. holes      ailes (os wing_l / wing_r) et bannieres (os banners) rendues en ortho de face et de dos : aucun pixel
              non couvert enferme dans la silhouette (trou parasite).
5. contract   fx_* vides, os craft_* ne contenant que des cubes glow*, tout dans x [-6.5, 6.5] y [0, 10] z [-3, 3].
Sortie : DEFECTS = n (statut 1 si n > 0).
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
sys.path.insert(0, os.path.join(HERE, "..", "doors"))
import preview as pv  # noqa: E402

ASSETS = os.path.abspath(os.path.join(HERE, "..", "..", "src/main/resources/assets/medievalships"))
GAP = 1.0 / 64


def load(name):
    with open(os.path.join(ASSETS, "models/entity/%s.bbmodel" % name)) as f:
        model = json.load(f)
    tex = np.array(Image.open(os.path.join(ASSETS, "textures/entity/%s.png" % name)).convert("RGBA"))
    return model, tex


def walk(model, fn):
    els = {e["uuid"]: e for e in model["elements"]}

    def rec(g, chain):
        chain = [g] + chain
        for ch in g["children"]:
            if isinstance(ch, dict):
                rec(ch, chain)
            else:
                fn(els[ch], chain)
    for g in model["outliner"]:
        rec(g, [])


def faces(model, tag):
    """Faces dessinees : (tag, nom element, face, coins 4x3 en blocs)."""
    out = []
    names = []

    def fn(e, chain):
        names.append(e["name"])
    walk(model, fn)
    quads = pv.build_mesh(model, {})
    # build_mesh parcourt les elements dans le meme ordre que walk ; on rattache les noms par element
    k = 0
    idx = []

    def fn2(e, chain):
        for fname, face in e["faces"].items():
            if face.get("texture") is not None:
                idx.append((e["name"], fname))
    walk(model, fn2)
    for (corners, uvs, glow, ti), (nm, fname) in zip(quads, idx):
        out.append((tag, nm, fname, np.array(corners)))
        k += 1
    return out


def _sat_overlap(P, Q):
    """Recouvrement (profondeur de penetration) de deux polygones convexes 2D, 0 si disjoints."""
    best = 1e9
    for poly in (P, Q):
        m = len(poly)
        for i in range(m):
            e = poly[(i + 1) % m] - poly[i]
            n = np.array([-e[1], e[0]])
            L = np.linalg.norm(n)
            if L < 1e-12:
                continue
            n /= L
            a, b = P @ n, Q @ n
            ov = min(a.max(), b.max()) - max(a.min(), b.min())
            if ov <= 1e-6:
                return 0.0
            best = min(best, ov)
    return best


def coplanar(fs, only_cross=False):
    recs = []
    for f in fs:
        c = f[3]
        n = np.cross(c[1] - c[0], c[3] - c[0])
        L = np.linalg.norm(n)
        if L < 1e-12:
            continue
        n /= L
        k = int(np.argmax(np.abs(n)))
        if n[k] < 0:
            n = -n
        d = float(n @ c.mean(axis=0))
        recs.append((tuple(np.round(n, 4)), d, n, f))
    buckets = {}
    for r in recs:
        buckets.setdefault((r[0], int(math.floor(r[1] * 64))), []).append(r)
    pairs = []
    for (nk, b), lst in buckets.items():
        for dd in (0, 1):
            other = buckets.get((nk, b + dd), [])
            for i, ra in enumerate(lst):
                for j, rb in enumerate(other):
                    if dd == 0 and j <= i:
                        continue
                    if abs(ra[1] - rb[1]) >= GAP - 1e-7:
                        continue
                    fa, fb = ra[3], rb[3]
                    if only_cross and fa[0] == fb[0]:
                        continue
                    if not only_cross and fa[0] != fb[0]:
                        continue
                    if fa[1] == fb[1] and fa[0] == fb[0] and np.allclose(fa[3].mean(0), fb[3].mean(0)) is False:
                        pass
                    n = ra[2]
                    u = np.cross(n, [0, 1, 0] if abs(n[1]) < 0.9 else [1, 0, 0])
                    u /= np.linalg.norm(u)
                    v = np.cross(n, u)
                    P = np.stack([fa[3] @ u, fa[3] @ v], 1)
                    Q = np.stack([fb[3] @ u, fb[3] @ v], 1)
                    if _sat_overlap(P, Q) > 1e-5:
                        pairs.append(("%s:%s/%s" % (fa[0], fa[1], fa[2]), "%s:%s/%s" % (fb[0], fb[1], fb[2]),
                                      round(abs(ra[1] - rb[1]), 5)))
    return pairs


def thin(model):
    bad = []
    for e in model["elements"]:
        s = np.abs(np.array(e["to"], float) - np.array(e["from"], float)) / 16
        if s.min() < GAP - 1e-9:
            bad.append((e["name"], round(float(s.min()), 5)))
    return bad


def transparent(model, tex):
    bad = []
    th, tw = tex.shape[:2]
    sx, sy = tw / model["resolution"]["width"], th / model["resolution"]["height"]
    for e in model["elements"]:
        if e["name"].startswith(("cut_", "glow_cut_")):
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
            if (blk < 255).any():
                bad.append((e["name"], fname))
    return bad


def find_groups(model, pred):
    out = []

    def rec(g):
        if pred(g["name"]):
            out.append(g)
        for ch in g["children"]:
            if isinstance(ch, dict):
                rec(ch)
    for g in model["outliner"]:
        rec(g)
    return out


def render(quads, texs, W, H, eye, target, fov=None, ortho=None, bg=(40, 40, 46), cov=False):
    import doorlib_small as ds
    return ds.render(quads, texs, W, H, eye, target, fov=fov, ortho=ortho, bg=bg, cov=cov)


def enclosed(cov):
    """Pixels non couverts qui ne communiquent pas avec le bord (trous enfermes)."""
    H, W = cov.shape
    free = ~cov
    seen = np.zeros_like(free)
    stack = [(j, i) for j in range(H) for i in (0, W - 1) if free[j, i]] + \
            [(j, i) for i in range(W) for j in (0, H - 1) if free[j, i]]
    for p in stack:
        seen[p] = True
    while stack:
        j, i = stack.pop()
        for dj, di in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            a, b = j + dj, i + di
            if 0 <= a < H and 0 <= b < W and free[a, b] and not seen[a, b]:
                seen[a, b] = True
                stack.append((a, b))
    return free & ~seen


def holes(model, tex, out_dir=None):
    res = {}
    ims = []
    for gname in ("wing_l", "wing_r", "banners"):
        gs = find_groups(model, lambda n, g=gname: n == g)
        if not gs:
            res[gname] = "absent"
            continue
        sub = dict(model, outliner=gs)
        quads = pv.build_mesh(json.loads(json.dumps(sub)), {})
        pts = np.concatenate([np.array(q[0]) for q in quads])
        lo, hi = pts.min(0), pts.max(0)
        c = (lo + hi) / 2
        for side, dz in (("face", 1), ("dos", -1)):
            if gname == "banners":
                # chaque banniere separement
                for sx in (-1, 1):
                    cc = np.array([sx * 5.6, c[1], c[2]])
                    span = (hi[1] - lo[1]) / 2 + 0.2
                    im, cv = render(quads, [tex], 128, int(256), cc + np.array([0, 0, 30 * dz]), cc, ortho=span, cov=True)
                    n = int(enclosed(cv).sum())
                    res["%s %+d %s" % (gname, sx, side)] = n
                    ims.append(im)
            else:
                span = max(hi[0] - lo[0], hi[1] - lo[1]) / 2 + 0.2
                im, cv = render(quads, [tex], 256, 256, c + np.array([0, 0, 30 * dz]), c, ortho=span, cov=True)
                res["%s %s" % (gname, side)] = int(enclosed(cv).sum())
                ims.append(im)
    if out_dir and ims:
        W = sum(i.size[0] for i in ims)
        sheet = Image.new("RGB", (W, max(i.size[1] for i in ims)), (0, 0, 0))
        x = 0
        for i in ims:
            sheet.paste(i, (x, 0))
            x += i.size[0]
        sheet.save(os.path.join(out_dir, "deco_audit_trous.png"))
    return res


def contract(model):
    errs = []
    for g in find_groups(model, lambda n: n.startswith("fx_")):
        if g["children"]:
            errs.append("%s non vide" % g["name"])
    els = {e["uuid"]: e for e in model["elements"]}
    for g in find_groups(model, lambda n: n.startswith("craft_")):
        def rec(gg):
            for ch in gg["children"]:
                if isinstance(ch, dict):
                    rec(ch)
                elif not els[ch]["name"].startswith("glow"):
                    errs.append("%s: cube non glow %s" % (g["name"], els[ch]["name"]))
        rec(g)
    for e in model["elements"]:
        for p in (e["from"], e["to"]):
            x, y, z = -p[0] / 16, p[1] / 16, -p[2] / 16
            if not (-6.5 - 1e-6 <= x <= 6.5 + 1e-6 and -1e-6 <= y <= 10 + 1e-6 and -3 - 1e-6 <= z <= 3 + 1e-6):
                errs.append("%s hors encombrement" % e["name"])
                break
    return errs


def main():
    args = sys.argv[1:]
    name = "forge_divine_deco"
    model, tex = load(name)
    out_dir = "/tmp/claude-0/-home-user-medieval-ships/2a9b6be4-7c0a-5b40-ad8d-40cfe82b9e67/scratchpad/forge_out"
    os.makedirs(out_dir, exist_ok=True)
    fs = faces(model, "B")
    res = {"coplanar": coplanar(fs), "thin": thin(model), "alpha": transparent(model, tex),
           "holes": holes(model, tex, out_dir), "contract": contract(model)}
    nh = sum(v for v in res["holes"].values() if isinstance(v, int))
    total = len(res["coplanar"]) + len(res["thin"]) + len(res["alpha"]) + nh + len(res["contract"])
    print("== %s : %d cubes, %d faces dessinees" % (name, len(model["elements"]), len(fs)))
    print("  coplanaires / paralleles < 1/64 :", len(res["coplanar"]), res["coplanar"][:12])
    print("  cubes trop fins :", len(res["thin"]), res["thin"][:8])
    print("  faces alpha < 255 :", len(res["alpha"]), res["alpha"][:8])
    print("  trous ailes / bannieres :", res["holes"])
    print("  contrat :", res["contract"] or "OK")
    if "--with" in args:
        other = args[args.index("--with") + 1]
        om, _ = load(other)
        fo = faces(om, "A")
        cross = coplanar(fs + fo, only_cross=True)
        print("== decor CONTRE %s : %d faces structure" % (other, len(fo)))
        print("  paires decor/structure :", len(cross), cross[:20])
        own = coplanar(fo)
        print("  (info) paires internes a la structure :", len(own), own[:6])
        total += len(cross)
    print("DEFECTS = %d" % total)
    sys.exit(1 if total else 0)



def sheet(path, tag="", with_structure=True):
    """Planche de controle : reference, vue de face (camera de l'image), 3/4, gros plan statue, decor seul."""
    ref = Image.open("/tmp/claude-0/-home-user-medieval-ships/2a9b6be4-7c0a-5b40-ad8d-40cfe82b9e67/scratchpad/"
                     "forge_ref/forge.png").convert("RGB")
    model, tex = load("forge_divine_deco")

    def strip(m, craft):
        m = json.loads(json.dumps(m))

        def rec(g):
            g["children"] = [c for c in g["children"] if not (isinstance(c, dict) and c["name"].startswith("craft_")
                                                                 and not craft)]
            for c in g["children"]:
                if isinstance(c, dict):
                    rec(c)
        for g in m["outliner"]:
            rec(g)
        return m
    qc = [(c, u, g, 0) for c, u, g, ti in pv.build_mesh(strip(model, True), {})]
    qd = pv.build_mesh(strip(model, False), {})
    texs = [tex.astype(float)]
    qs = []
    if with_structure and os.path.exists(os.path.join(ASSETS, "models/entity/forge_divine.bbmodel")):
        sm, stex = load("forge_divine")
        qs = [(c, u, g, 1) for c, u, g, ti in pv.build_mesh(strip(sm, False), {})]
        texs.append(stex.astype(float))
    qd = [(c, u, g, 0) for c, u, g, ti in qd]
    W, H = 768, 512
    views = [("face (camera de l'image)", qd + qs, (0, 15.5, 29), (0, 4.6, 0), 21),
             ("3/4", qd + qs, (17, 10.5, 27), (0, 4.4, 0), 24),
             ("statue gros plan (repos)", qd + qs, (2.0, 9.4, 6.0), (0, 8.15, -0.5), 30),
             ("statue gros plan (fabrication : craft_*)", qc + qs, (-2.0, 9.4, 6.0), (0, 8.15, -0.5), 30),
             ("decor seul, face", qd, (0, 15.5, 29), (0, 4.6, 0), 21)]
    ims = [("reference", ref.resize((W, H), Image.LANCZOS))]
    for title, quads, eye, target, fov in views:
        ims.append((title, render(quads, texs, W, H, eye, target, fov=fov, bg=(46, 44, 48))))
    from PIL import ImageDraw
    cols = 2
    rows = (len(ims) + 1) // 2
    out = Image.new("RGB", (W * cols, (H + 20) * rows), (20, 20, 22))
    d = ImageDraw.Draw(out)
    for i, (t, im) in enumerate(ims):
        x, y = (i % cols) * W, (i // cols) * (H + 20)
        out.paste(im, (x, y + 20))
        d.text((x + 6, y + 4), "%s %s" % (t, tag), fill=(240, 220, 160))
    out.save(path)
    return path


if __name__ == "__main__":
    if "--sheet" in sys.argv:
        print(sheet(sys.argv[sys.argv.index("--sheet") + 1], " ".join(a for a in sys.argv[1:] if a.startswith("it"))))
    else:
        main()
