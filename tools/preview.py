#!/usr/bin/env python3
"""Software renderer for the galley .bbmodel (reference implementation of the
mod's model loader: same transform, UV and animation rules).

Usage: python3 tools/preview.py [model.bbmodel] [texture.png] [out.png] [--anim row=0.5,steer=1.6]
"""
import base64
import io
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def rot_zyx(deg):
    a, b, c = [math.radians(d) for d in deg]
    ca, sa, cb, sb, cc, sc = math.cos(a), math.sin(a), math.cos(b), math.sin(b), math.cos(c), math.sin(c)
    Rx = np.array([[1, 0, 0], [0, ca, -sa], [0, sa, ca]])
    Ry = np.array([[cb, 0, sb], [0, 1, 0], [-sb, 0, cb]])
    Rz = np.array([[cc, -sc, 0], [sc, cc, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


FACES = {  # normal, u dir, v dir
    "north": ((0, 0, -1), (-1, 0, 0), (0, -1, 0)),
    "south": ((0, 0, 1), (1, 0, 0), (0, -1, 0)),
    "west": ((-1, 0, 0), (0, 0, 1), (0, -1, 0)),
    "east": ((1, 0, 0), (0, 0, -1), (0, -1, 0)),
    "up": ((0, 1, 0), (1, 0, 0), (0, 0, 1)),
    "down": ((0, -1, 0), (1, 0, 0), (0, 0, -1)),
}


def sample_channel(kfs, t):
    kfs = sorted(kfs, key=lambda k: k["time"])
    vals = [(k["time"], np.array([float(k["data_points"][0][a]) for a in "xyz"])) for k in kfs]
    if t <= vals[0][0]:
        return vals[0][1]
    for i in range(len(vals) - 1):
        t0, v0 = vals[i]
        t1, v1 = vals[i + 1]
        if t0 <= t <= t1:
            f = 0 if t1 == t0 else (t - t0) / (t1 - t0)
            return v0 + (v1 - v0) * f
    return vals[-1][1]


def bone_pose(model, anim_times):
    """bone name -> (rot_add_deg, pos_add_px, scale)"""
    pose = {}
    for anim in model.get("animations", []):
        if anim["name"] not in anim_times:
            continue
        t = anim_times[anim["name"]]
        for an in anim["animators"].values():
            name = an["name"]
            rot, pos, scl = pose.get(name, (np.zeros(3), np.zeros(3), np.ones(3)))
            by = {}
            for k in an["keyframes"]:
                by.setdefault(k["channel"], []).append(k)
            if "rotation" in by:
                r = sample_channel(by["rotation"], t)
                rot = rot + r
            if "position" in by:
                p = sample_channel(by["position"], t)
                pos = pos + p
            if "scale" in by:
                scl = scl * sample_channel(by["scale"], t)
            pose[name] = (rot, pos, scl)
    return pose


def build_mesh(model, anim_times=None):
    anim_times = anim_times or {}
    pose = bone_pose(model, anim_times)
    elements = {e["uuid"]: e for e in model["elements"]}
    quads = []  # (4 pts local blocks, 4 uv, glow)

    def walk(group, chain):
        chain = [group] + chain
        for ch in group["children"]:
            if isinstance(ch, dict):
                walk(ch, chain)
            else:
                emit(elements[ch], chain)

    def transform(p, chain):
        for g in chain:
            o = np.array(g["origin"], dtype=float)
            rot = np.array(g.get("rotation", [0, 0, 0]), dtype=float)
            r_add, p_add, s = pose.get(g["name"], (np.zeros(3), np.zeros(3), np.ones(3)))
            R = rot_zyx(rot + r_add)
            p = R @ ((p - o) * s) + o + p_add
        return p

    def emit(e, chain):
        f, t = np.array(e["from"], float), np.array(e["to"], float)
        o = np.array(e.get("origin", [0, 0, 0]), float)
        R = rot_zyx(e.get("rotation", [0, 0, 0]))
        glow = e["name"].startswith("glow")
        for fname, face in e["faces"].items():
            if face.get("texture") is None:
                continue
            n, ud, vd = [np.array(x, float) for x in FACES[fname]]
            # corners in order (u0,v0) (u1,v0) (u1,v1) (u0,v1)
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
                p = R @ (p - o) + o
                p = transform(p, chain)
                corners.append(np.array([-p[0] / 16, p[1] / 16, -p[2] / 16]))
                uvs.append((u1 + (u2 - u1) * cu, v1 + (v2 - v1) * cv))
            quads.append((corners, uvs, glow))

    for g in model["outliner"]:
        walk(g, [])
    return quads


def render(quads, tex, W, H, eye, target, fov=None, ortho=None, bg=(28, 33, 48)):
    eye, target = np.array(eye, float), np.array(target, float)
    fwd = target - eye
    fwd /= np.linalg.norm(fwd)
    up = np.array([0, 1, 0.0]) if abs(fwd[1]) < 0.99 else np.array([0, 0, 1.0])
    right = np.cross(fwd, up)
    right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    img = np.zeros((H, W, 3), float)
    img[:] = bg
    zbuf = np.full((H, W), np.inf)
    tw, th = tex.shape[1], tex.shape[0]
    light = np.array([0.4, 0.8, -0.45])
    light /= np.linalg.norm(light)

    def project(p):
        d = p - eye
        x, y, z = d @ right, d @ up, d @ fwd
        if ortho:
            s = W / ortho
            return np.array([W / 2 + x * s, H / 2 - y * s, z])
        f = (H / 2) / math.tan(math.radians(fov) / 2)
        return np.array([W / 2 + x * f / z, H / 2 - y * f / z, z])

    for corners, uvs, glow in quads:
        P = [project(c) for c in corners]
        n = np.cross(corners[1] - corners[0], corners[3] - corners[0])
        nn = np.linalg.norm(n)
        if nn < 1e-9:
            continue
        n /= nn
        shade = 1.0 if glow else 0.55 + 0.45 * abs(float(n @ light))
        for tri in ((0, 1, 2), (0, 2, 3)):
            a, b, c = (P[i] for i in tri)
            if min(a[2], b[2], c[2]) <= 0.05:
                continue
            ua, ub, uc = (np.array(uvs[i]) for i in tri)
            xmin, xmax = int(max(0, math.floor(min(a[0], b[0], c[0])))), int(min(W - 1, math.ceil(max(a[0], b[0], c[0]))))
            ymin, ymax = int(max(0, math.floor(min(a[1], b[1], c[1])))), int(min(H - 1, math.ceil(max(a[1], b[1], c[1]))))
            if xmin > xmax or ymin > ymax:
                continue
            xs, ys = np.meshgrid(np.arange(xmin, xmax + 1) + 0.5, np.arange(ymin, ymax + 1) + 0.5)
            det = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
            if abs(det) < 1e-9:
                continue
            w0 = ((b[1] - c[1]) * (xs - c[0]) + (c[0] - b[0]) * (ys - c[1])) / det
            w1 = ((c[1] - a[1]) * (xs - c[0]) + (a[0] - c[0]) * (ys - c[1])) / det
            w2 = 1 - w0 - w1
            mask = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
            if not mask.any():
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
            tx = np.clip(np.floor(uu).astype(int), 0, tw - 1)
            ty = np.clip(np.floor(vv).astype(int), 0, th - 1)
            col = tex[ty, tx]
            mask &= col[..., 3] > 127
            sub = zbuf[ymin:ymax + 1, xmin:xmax + 1]
            mask &= z < sub
            if not mask.any():
                continue
            sub[mask] = z[mask]
            region = img[ymin:ymax + 1, xmin:xmax + 1]
            region[mask] = col[..., :3][mask] * shade
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    model_path = args[0] if len(args) > 0 else os.path.join(ROOT, "blockbench/galley.bbmodel")
    out = args[2] if len(args) > 2 else os.path.join(ROOT, "docs/preview.png")
    anim = {"sail_furl": 0.0, "steer": 1.0, "row": 0.3, "flag_wave": 0.2, "streamer_wave": 0.3}
    for a in sys.argv[1:]:
        if a.startswith("--anim="):
            for kv in a[7:].split(","):
                k, v = kv.split("=")
                anim[k] = float(v)
    model = json.load(open(model_path))
    if len(args) > 1:
        tex = np.array(Image.open(args[1]).convert("RGBA")).astype(float)
    else:
        src = model["textures"][0]["source"].split(",", 1)[1]
        tex = np.array(Image.open(io.BytesIO(base64.b64decode(src))).convert("RGBA")).astype(float)
    quads = build_mesh(model, anim)
    tgt = (0, 4.5, 0)
    views = [
        ("Vue Perspective", dict(W=900, H=560, eye=(-22, 11, 17), target=(0, 4.0, 0.5), fov=50)),
        ("Vue Avant", dict(W=440, H=560, eye=(0, 3.5, 60), target=(0, 6, 0), ortho=17)),
        ("Vue Arriere", dict(W=440, H=560, eye=(0, 3.5, -60), target=(0, 6, 0), ortho=17)),
        ("Vue Droite", dict(W=900, H=480, eye=(-60, 5, 0), target=(0, 5.5, 0), ortho=31)),
        ("Vue Gauche", dict(W=900, H=480, eye=(60, 5, 0), target=(0, 5.5, 0), ortho=31)),
        ("Vue Dessus", dict(W=440, H=480, eye=(0, 60, 0.01), target=(0, 0, 0), ortho=26)),
    ]
    imgs = []
    for title, kw in views:
        im = render(quads, tex, **kw)
        ImageDraw.Draw(im).text((12, 10), title, fill=(235, 225, 200))
        imgs.append(im)
    sheet = Image.new("RGB", (900 + 440 + 440, 560 + 480), (28, 33, 48))
    sheet.paste(imgs[0], (0, 0))
    sheet.paste(imgs[1], (900, 0))
    sheet.paste(imgs[2], (1340, 0))
    sheet.paste(imgs[3], (0, 560))
    sheet.paste(imgs[4].resize((440, 235)), (900, 560))
    sheet.paste(imgs[5].resize((440, 480)), (1340, 560))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    sheet.save(out)
    print("wrote", out, "quads:", len(quads))


if __name__ == "__main__":
    main()
