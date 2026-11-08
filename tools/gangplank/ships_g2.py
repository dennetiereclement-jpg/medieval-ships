"""Gangplanks (passerelles) of the ships and large airships other than the two reference vessels (trade_sloop and
steampunk_airship, see gangplanklib.py / core/Gangplank.java): their specs, plank models and verification renders.

    python3 tools/gangplank/ships_g2.py specs            # writes assets/medievalships/gangplanks/<id>.json
    python3 tools/gangplank/ships_g2.py models           # gangplank_<id>.bbmodel (+ the levers of the styles used)
    python3 tools/gangplank/ships_g2.py probe <id> ys zs # outer face of the hull model at (y, z) on both sides
    python3 tools/gangplank/ships_g2.py deck <id> xs zs  # model surfaces under (x, z) (TOP=<y> to start lower)
    python3 tools/gangplank/ships_g2.py sheet <out.png> [ids...]   # contact sheet: one row per vessel (before / after)
    python3 tools/gangplank/ships_g2.py single <dir> ids...        # the 640x480 views of each vessel
    python3 tools/gangplank/ships_g2.py stow [ids...]              # model surface under the hinge (stow_offset)

Frame: the ship-local frame of core/Gangplank.java (+x port, y up, +z bow, blocks; the frame preview.py emits).

How each plank was placed (see also docs/PASSERELLES_NAVIRES.md):
- the hinge is on the outer face of the hull (or of its bulwark) at a clear stretch of the side: between gun ports,
  oars, shrouds, paddle boxes, benches, hatches and windows;
- its height is the top of the rail (open ships) or of the bulwark (interior grid; the model's rail cap when it is
  higher), so nothing above it blocks the way; open ships also get a rail gap over the plank's width;
- the step box fills from the deck up to the hinge height against the bulwark: core/Gangplank.stairBoxes turns it into
  stairs of at most 0.45 (one per 0.45 of rise, 0.45 deep each);
- the lever stands on the deck beside the stairs (never on them), within 4 blocks of the hinge;
- the length lets the plank reach a quay one block above the water (ships) within its slope limits, or a landing
  platform about 3.9 blocks under the deck (airships, whose max_drop is the platform reach);
- stowed, the plank folds like an accordion into a pack hanging against the hull side under the hinge (1.23.1):
  stow_offset is the outermost surface of the ship model over the pack's height and width, outboard of the hinge line
  (`stow` measures it; core/Gangplank.fold keeps the pack STOW_CLEARANCE beyond it, or beyond the hull shape if that
  stands further out); segments overrides the number of folding segments (the medieval galley's 4 keep its pack
  above the oar ports).
GangplankSpecsTest (JUnit) checks all of this against the ships' geometry.
"""
import base64
import io
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.abspath(os.path.join(HERE, ".."))
ROOT = os.path.abspath(os.path.join(TOOLS, ".."))
sys.path.insert(0, TOOLS)
sys.path.insert(0, HERE)
ASSETS = os.path.join(ROOT, "src/main/resources/assets/medievalships")
MODELS = os.path.join(ASSETS, "models/entity")

# --------------------------------------------------------------------------------------------- the specs
# side, hinge, width, length, style, lever, step, rail_gap, angles, max_drop, chain_anchor (+ optional lever_yaw,
# stowed_angle, handrails). Filled from the layouts (core/*Layout.java, core/Ships.java), the interior grids and the
# models; see the module doc for the rules.
SPECS = {}


def spec(ship, **kw):
    SPECS[ship] = kw


# placed here for reference only: no gangplank (the player asked for none), its spec and model are not written
NOT_EQUIPPED = {"nautilus"}


def write_specs(ids=None):
    d = os.path.join(ASSETS, "gangplanks")
    os.makedirs(d, exist_ok=True)
    for ship, s in SPECS.items():
        if (ids and ship not in ids) or ship in NOT_EQUIPPED:
            continue
        out = {}
        for k in ("side", "hinge", "width", "length", "style", "lever", "lever_yaw", "step", "rail_gap", "angles",
                  "max_drop", "chain_anchor", "stowed_angle", "handrails", "segments", "stow_offset"):
            if k in s:
                v = s[k]
                if isinstance(v, (list, tuple)):
                    v = [round(float(x), 3) for x in v]
                elif isinstance(v, float):
                    v = round(v, 3)
                out[k] = v
        with open(os.path.join(d, ship + ".json"), "w") as f:
            json.dump(out, f, indent=2)
            f.write("\n")
        print("gangplanks/%s.json" % ship)


def make_models(ids=None):
    import gangplanklib as gp
    styles = set()
    for ship, s in SPECS.items():
        if (ids and ship not in ids) or ship in NOT_EQUIPPED:
            continue
        gp.make_plank(ship, s["width"], s["length"], s["style"], handrails=s.get("handrails", True), segments=s.get("segments"))
        styles.add(s["style"])
    for st in sorted(styles):
        if not os.path.exists(os.path.join(MODELS, "gangplank_lever_%s.bbmodel" % st)):
            gp.make_lever(st)


# --------------------------------------------------------------------------------------------- geometry helpers
def load_model(name):
    import preview
    with open(os.path.join(MODELS, name + ".bbmodel")) as f:
        model = json.load(f)
    from PIL import Image
    tex = [np.array(Image.open(io.BytesIO(base64.b64decode(t["source"].split(",", 1)[1]))).convert("RGBA")).astype(float)
           for t in model["textures"]]
    return preview.build_mesh(model, {}), tex


def _tris(quads):
    a, b, c = [], [], []
    for corners, _uv, _g, _t in quads:
        p = corners
        a += [p[0], p[0]]
        b += [p[1], p[2]]
        c += [p[2], p[3]]
    return np.array(a), np.array(b), np.array(c)


def raycast(tris, origin, d):
    """Distances along d to every triangle hit (Moller-Trumbore), sorted."""
    a, b, c = tris
    e1, e2 = b - a, c - a
    d = np.asarray(d, float)
    p = np.cross(d, e2)
    det = np.einsum("ij,ij->i", e1, p)
    ok = np.abs(det) > 1e-12
    inv = np.where(ok, 1.0 / np.where(ok, det, 1), 0)
    s = np.asarray(origin, float) - a
    u = np.einsum("ij,ij->i", s, p) * inv
    q = np.cross(s, e1)
    v = (q @ d) * inv
    t = np.einsum("ij,ij->i", e2, q) * inv
    hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 0)
    return np.sort(t[hit])


def probe(ship, pts):
    """For each (y, z): x of the outermost model surface on the port (+x) and starboard (-x) sides."""
    quads, _ = load_model(ship)
    tris = _tris(quads)
    for y, z in pts:
        tp = raycast(tris, (40, y, z), (-1, 0, 0))
        ts = raycast(tris, (-40, y, z), (1, 0, 0))
        print("y=%.2f z=%.2f  port x=%s  starboard x=%s" % (y, z, "%.2f" % (40 - tp[0]) if len(tp) else "-",
                                                             "%.2f" % (-40 + ts[0]) if len(ts) else "-"))


def deck_probe(ship, pts, top=float(os.environ.get("TOP", 30))):
    """For each (x, z): heights of the model surfaces hit by a ray going down from y = top."""
    quads, _ = load_model(ship)
    tris = _tris(quads)
    for x, z in pts:
        t = raycast(tris, (x, top, z), (0, -1, 0))
        print("x=%.2f z=%.2f  surfaces y=%s" % (x, z, " ".join("%.2f" % (top - v) for v in t[:6])))


# --------------------------------------------------------------------------------------------- verification renders
def plank_point(s, a, u, v, w):
    """core/Gangplank.Spec.point: ship-local point of the plank at angle a (degrees, down positive)."""
    o = 1 if s["side"] == "port" else -1
    hx, hy, hz = s["hinge"]
    r = math.radians(a)
    c, sn = math.cos(r), math.sin(r)
    return np.array([hx + o * (u * c + v * sn), hy - u * sn + v * c, hz + o * w])


# ---- the accordion folding, as core/Gangplank.java (fold, foldPose, foldPoint, railPoint)
STOW_CLEARANCE, STOW_DROP, HANG, RAISE = 0.06, 0.12, 90.0, 20.0
UNLOCK, SETTLE, LIFT_END, UNFOLD_START, UNFOLD_END, LOWER_START, RAIL_START = 0.1, 0.12, 0.40, 0.30, 0.76, 0.62, 0.76


def _ease(t):
    t = max(0.0, min(1.0, t))
    return 4 * t * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def fold_of(ship, s):
    """core/Gangplank.fold. The hull shape is Java only: the specs' stow_offset is at least the hull's standoff
    (STOW_OFFSET is rounded up from both), so max(stow_offset, hull) is stow_offset here as in game."""
    import gangplanklib as gp
    n = gp.segment_count(s["length"], s.get("segments"))
    seg = s["length"] / n
    standoff = s.get("stow_offset", 0.0) + STOW_CLEARANCE
    return dict(n=n, seg=seg, standoff=standoff, offX=standoff + gp.FOLD_UNDER, offY=-STOW_DROP)


def joint_opening(p, j, n):
    m = n - 1
    span = UNFOLD_END - UNFOLD_START
    w = span if m <= 1 else span * 0.5
    start = UNFOLD_START if m <= 1 else UNFOLD_START + (j - 1) * (span - w) / (m - 1)
    return _ease((p - start) / w)


def fold_pose(f, p, target):
    """core/Gangplank.foldPose: [(a_k, cx_k, cy_k)] per segment and the handrail fold (degrees)."""
    import gangplanklib as gp
    n, s = f["n"], f["seg"]
    raised = min(target, 0.0) - RAISE
    swing_end = 1.0 - SETTLE
    if p <= 0:
        a0, g = HANG, 1.0
    elif p < UNLOCK:
        a0, g = HANG - 3.0 * math.sin(math.pi * p / UNLOCK), 1.0
    elif p < LIFT_END:
        e = _ease((p - UNLOCK) / (LIFT_END - UNLOCK))
        a0, g = HANG + (raised - HANG) * e, 1 - e
    elif p < LOWER_START:
        a0, g = raised, 0.0
    elif p < swing_end:
        a0, g = raised + (target - raised) * _ease((p - LOWER_START) / (swing_end - LOWER_START)), 0.0
    elif p < 1:
        r = (p - swing_end) / SETTLE
        a0, g = target - 1.5 * math.sin(math.pi * r) * (1 - r * 0.5), 0.0
    else:
        a0, g = target, 0.0
    pose = [(a0, g * f["offX"], g * f["offY"])]
    for j in range(1, n):
        top = j % 2 == 1
        theta = (-180.0 if top else 180.0) * (1.0 - (1.0 if p >= 1 else joint_opening(p, j, n)))
        pu, pv = j * s, (gp.FOLD_OVER if top else -gp.FOLD_UNDER)
        ap, cx, cy = pose[-1]
        c, sn = math.cos(math.radians(ap)), math.sin(math.radians(ap))
        wx, wy = cx + pu * c + pv * sn, cy - pu * sn + pv * c
        ak = ap + theta
        ck, sk = math.cos(math.radians(ak)), math.sin(math.radians(ak))
        pose.append((ak, wx - (pu * ck + pv * sk), wy - (-pu * sk + pv * ck)))
    rail = 0.0 if p >= 1 else 90.0 * (1.0 - _ease((p - RAIL_START) / (1.0 - SETTLE - RAIL_START)))
    return pose, rail


def fold_point(s, pose, k, u, v, w):
    o = 1 if s["side"] == "port" else -1
    hx, hy, hz = s["hinge"]
    a, cx, cy = pose[k]
    c, sn = math.cos(math.radians(a)), math.sin(math.radians(a))
    return np.array([hx + o * (cx + u * c + v * sn), hy + cy - u * sn + v * c, hz + o * w])


def rail_point(s, side, fold, p):
    import gangplanklib as gp
    pz = side * (s["width"] / 2 - gp.RAIL_PIVOT_INSET)
    psi = math.radians(-side * fold)
    c, sn = math.cos(psi), math.sin(psi)
    dv, dw = p[1] - gp.RAIL_PIVOT_V, p[2] - pz
    return np.array([p[0], gp.RAIL_PIVOT_V + dv * c - dw * sn, pz + dv * sn + dw * c])


def part_quads(model, name, children=False):
    """Quads (model-local) of one bone of a model, with or without its child bones."""
    import preview

    def find(g):
        if g["name"] == name:
            return g
        for c in g["children"]:
            if isinstance(c, dict):
                r = find(c)
                if r is not None:
                    return r
        return None
    g = find(model["outliner"][0])
    if g is None:
        return []
    g2 = dict(g)
    if not children:
        g2["children"] = [c for c in g["children"] if not isinstance(c, dict)]
    m2 = dict(model)
    m2["outliner"] = [g2]
    return preview.build_mesh(m2, {})


def plank_parts(ship):
    """{"seg_k": quads, "rail_k_s": quads} of a folding plank model, and its texture."""
    with open(os.path.join(MODELS, "gangplank_" + ship + ".bbmodel")) as f:
        model = json.load(f)
    from PIL import Image
    tex = [np.array(Image.open(io.BytesIO(base64.b64decode(t["source"].split(",", 1)[1]))).convert("RGBA")).astype(float)
           for t in model["textures"]]
    parts = {}
    k = 0
    while True:
        q = part_quads(model, "seg_%d" % k)
        if not q:
            break
        parts["seg_%d" % k] = q
        for side in (0, 1):
            parts["rail_%d_%d" % (k, side)] = part_quads(model, "rail_%d_%d" % (k, side), children=True)
        k += 1
    return parts, tex


def folded_quads(s, parts, pose, rail, tex_offset):
    out = []
    for name, quads in parts.items():
        bits = name.split("_")
        k = int(bits[1])
        side = (1 if bits[2] == "1" else -1) if bits[0] == "rail" else 0
        for corners, uvs, glow, ti in quads:
            pts = []
            for p in corners:
                if side:
                    p = rail_point(s, side, rail, p)
                pts.append(fold_point(s, pose, k, p[0], p[1], p[2]))
            out.append((pts, uvs, glow, ti + tex_offset))
    return out


def lever_quads(s, lever, tex_offset):
    out = []
    th = math.radians(lever_yaw(s))
    c, sn = math.cos(th), math.sin(th)
    lx, ly, lz = s["lever"]
    for corners, uvs, glow, ti in lever:
        out.append(([np.array([lx + p[0] * c + p[2] * sn, ly + p[1], lz - p[0] * sn + p[2] * c]) for p in corners],
                    uvs, glow, ti + tex_offset))
    return out


def lever_yaw(s):
    if "lever_yaw" in s:
        return s["lever_yaw"]
    return 0.0 if s["side"] == "starboard" else 180.0


def placed_quads(s, plank, lever, angle, tex_offset):
    """The one-piece plank (1.23.0) at an angle, and the lever."""
    out = []
    for corners, uvs, glow, ti in plank:
        out.append(([plank_point(s, angle, p[0], p[1], p[2]) for p in corners], uvs, glow, ti + tex_offset))
    return out + lever_quads(s, lever, tex_offset)


POST, POST_HEIGHT, STAIR_RISE = 0.13, 2.5, 0.45   # as GangplankRenderer / core/Gangplank.java


def _uvq(reg):
    u0, v0, w0, h0 = reg
    return [(u0, v0), (u0 + w0, v0), (u0 + w0, v0 + h0), (u0, v0 + h0)]


def _box_quads(x0, y0, z0, x1, y1, z1, reg, ti):
    """The six faces of an axis-aligned box (ship-local)."""
    x0, x1 = min(x0, x1), max(x0, x1)
    y0, y1 = min(y0, y1), max(y0, y1)
    z0, z1 = min(z0, z1), max(z0, z1)
    P = lambda x, y, z: np.array([x, y, z], float)  # noqa: E731
    faces = [
        [P(x0, y1, z0), P(x1, y1, z0), P(x1, y1, z1), P(x0, y1, z1)],
        [P(x0, y0, z1), P(x1, y0, z1), P(x1, y0, z0), P(x0, y0, z0)],
        [P(x0, y1, z1), P(x1, y1, z1), P(x1, y0, z1), P(x0, y0, z1)],
        [P(x1, y1, z0), P(x0, y1, z0), P(x0, y0, z0), P(x1, y0, z0)],
        [P(x1, y1, z1), P(x1, y1, z0), P(x1, y0, z0), P(x1, y0, z1)],
        [P(x0, y1, z0), P(x0, y1, z1), P(x0, y0, z1), P(x0, y0, z0)],
    ]
    return [(f, _uvq(reg), False, ti) for f in faces]


def stair_boxes(s):
    """core/Gangplank.stairBoxes: the step box as stairs of at most STAIR_RISE rising towards the hull side."""
    st = s.get("step")
    if not st:
        return []
    x0, y0, z0, x1, y1, z1 = min(st[0], st[3]), min(st[1], st[4]), min(st[2], st[5]), max(st[0], st[3]), max(st[1], st[4]), max(st[2], st[5])
    rise = y1 - y0
    n = max(1, int(math.ceil(rise / STAIR_RISE - 1e-9)))
    depth = (x1 - x0) / n
    out = []
    for k in range(n):
        top = y0 + rise * (k + 1) / n
        if s["side"] == "port":
            out.append((x0 + depth * k, y0, z0, x1, top, z1))
        else:
            out.append((x0, y0, z0, x1 - depth * k, top, z1))
    return out


def chain_quads(s, tip, tex_offset, deployed):
    """Stand-in for what GangplankRenderer draws besides the models: the two chains / ropes (from the chain anchor, or
    from a small gallows post at each end of the hinge) to tip(w) (the plank's outer corner eyes) and, while the plank
    is out, the inboard stairs."""
    import gangplanklib as gp
    o = 1 if s["side"] == "port" else -1
    cord, rail, metal = (gp.REGIONS["%s_%s" % (s["style"], k)] for k in ("cord", "rail", "metal"))
    plank_top, board = gp.REGIONS["%s_plank" % s["style"]], gp.REGIONS["%s_board" % s["style"]]
    out = []
    hx, hy, hz = s["hinge"]
    hw = s["width"] / 2 - 0.08
    for w in (-hw, hw):
        if s.get("chain_anchor"):
            ax, ay, az = s["chain_anchor"]
            a = np.array([ax, ay, az + o * w])
        else:
            px, pz = hx - o * 0.12, hz + o * (w + math.copysign(0.2, w))
            out += _box_quads(px - POST / 2, hy - 0.1, pz - POST / 2, px + POST / 2, hy + POST_HEIGHT, pz + POST / 2, rail, tex_offset)
            out += _box_quads(px - 0.1, hy + POST_HEIGHT - 0.2, pz - 0.1, px + 0.1, hy + POST_HEIGHT + 0.04, pz + 0.1, metal, tex_offset)
            a = np.array([px, hy + POST_HEIGHT - 0.08, pz])
        b = tip(w)
        d = b - a
        n = np.linalg.norm(d)
        if n < 1e-6:
            continue
        d /= n
        e = np.cross(d, [0, 0, 1.0])
        if np.linalg.norm(e) < 1e-6:
            e = np.cross(d, [1.0, 0, 0])
        e = e / np.linalg.norm(e) * 0.025
        f = np.cross(d, e)
        f = f / np.linalg.norm(f) * 0.025
        for g in (e, f):
            out.append(([a - g, b - g, b + g, a + g], _uvq(cord), False, tex_offset))
    if deployed:
        for (x0, y0, z0, x1, y1, z1) in stair_boxes(s):
            out += _box_quads(x0, y0, z0, x1, y1 - 0.06, z1, board, tex_offset)
            out += _box_quads(x0 - 0.02, y1 - 0.06, z0 - 0.02, x1 + 0.02, y1, z1 + 0.02, plank_top, tex_offset)
    return out


def folded_scene(ship, s, parts, lever, off, p, target):
    f = fold_of(ship, s)
    pose, rail = fold_pose(f, p, target)
    k = f["n"] - 1
    tip = lambda w: fold_point(s, pose, k, s["length"] - 0.25, 0.06, w)  # noqa: E731
    return folded_quads(s, parts, pose, rail, off) + lever_quads(s, lever, off) + chain_quads(s, tip, off, p > 0)


def render_views(ship, s, ship_mesh=None, size=(640, 480), old_plank=None):
    """[(title, image)]: (with old_plank, the one-piece plank of 1.23.0 stowed upright: "avant"), the folded pack stowed
    (same camera), the pack close up from outboard, half deployed (unfolding), deployed at 20 degrees. Ship-local space,
    centred on the hinge."""
    import preview
    from PIL import ImageDraw
    quads, tex = ship_mesh or load_model(ship)
    parts, ptex = plank_parts(ship)
    lever, _ = load_model("gangplank_lever_" + s["style"])
    off = len(tex)
    textures = list(tex) + [ptex[0]]
    o = 1 if s["side"] == "port" else -1
    hx, hy, hz = s["hinge"]
    L = s["length"]
    W, H = size
    hinge = np.array([hx, hy, hz])
    k = max(4.0, L)
    eye34 = hinge + np.array([o * 1.25 * k, 0.8 * k, 1.05 * k])
    tgt_old = tuple(hinge + np.array([0, 0.4 * L, 0]))
    views = []
    if old_plank is not None:
        tip = lambda w: plank_point(s, -90.0, L - 0.25, 0.06, w)  # noqa: E731
        old = placed_quads(s, old_plank, lever, -90.0, off) + chain_quads(s, tip, off, False)
        views.append(("avant : rangee (1.23.0)", preview.render(quads + old, textures, W, H, eye=tuple(eye34), target=tgt_old, fov=55)))
    stowed = folded_scene(ship, s, parts, lever, off, 0.0, 20.0)
    views.append(("apres : rangee", preview.render(quads + stowed, textures, W, H, eye=tuple(eye34), target=tgt_old, fov=55)))
    f = fold_of(ship, s)
    pack = hinge + np.array([o * (f["standoff"] + f["n"] * 0.2), -0.9, 0])
    eye_c = pack + np.array([o * 4.5, 1.6, 3.2])
    views.append(("apres : paquet replie", preview.render(quads + stowed, textures, W, H, eye=tuple(eye_c), target=tuple(pack), fov=50)))
    tgt34 = hinge + np.array([o * 0.35 * L, -0.25 * L, 0])
    half = folded_scene(ship, s, parts, lever, off, 0.5, 20.0)
    views.append(("depliage (mi-course)", preview.render(quads + half, textures, W, H, eye=tuple(eye34), target=tuple(tgt34), fov=55)))
    deployed = folded_scene(ship, s, parts, lever, off, 1.0, 20.0)
    views.append(("deployee 20 deg", preview.render(quads + deployed, textures, W, H, eye=tuple(eye34), target=tuple(tgt34), fov=55)))
    for title, im in views:
        ImageDraw.Draw(im).text((8, 6), "%s - %s" % (ship, title), fill=(255, 240, 160))
    return views


def old_plank_mesh(ship):
    """The one-piece plank model of 1.23.0 (git show 75d23ffc), for the before / after sheet; None if unavailable."""
    import subprocess
    import preview
    try:
        raw = subprocess.check_output(["git", "-C", ROOT, "show", "75d23ffc:src/main/resources/assets/medievalships/models/entity/gangplank_%s.bbmodel" % ship])
    except Exception:
        return None
    return preview.build_mesh(json.loads(raw), {})


def sheet(out, ids):
    from PIL import Image, ImageDraw
    cw, ch = 320, 240
    rows = []
    for ship in ids:
        s = SPECS[ship] if ship in SPECS else load_spec(ship)
        views = render_views(ship, s, old_plank=old_plank_mesh(ship))
        row = Image.new("RGB", (cw * len(views), ch), (20, 22, 30))
        for i, (_t, im) in enumerate(views):
            row.paste(im.resize((cw, ch), Image.LANCZOS), (i * cw, 0))
        rows.append(row)
        print("rendered", ship, flush=True)
    img = Image.new("RGB", (max(r.width for r in rows), ch * len(rows)), (20, 22, 30))
    for i, r in enumerate(rows):
        img.paste(r, (0, i * ch))
        ImageDraw.Draw(img).line([(0, i * ch), (img.width, i * ch)], fill=(70, 70, 90))
    img.save(out)
    print("wrote", out)


def single(ship, outdir):
    """The 640x480 views of one vessel, for close inspection."""
    s = SPECS[ship] if ship in SPECS else load_spec(ship)
    for i, (_t, im) in enumerate(render_views(ship, s, old_plank=old_plank_mesh(ship))):
        im.save(os.path.join(outdir, "%s_%d.png" % (ship, i)))
    print("rendered", ship)


def stow_probe(ship, s=None):
    """Outermost surface of the ship model over the stowed pack's height and width, outboard of the hinge line (the
    spec's stow_offset should be at least this; core/Gangplank.fold adds STOW_CLEARANCE). Returns (max, rows)."""
    import gangplanklib as gp
    s = s or (SPECS[ship] if ship in SPECS else load_spec(ship))
    o = 1 if s["side"] == "port" else -1
    hx, hy, hz = s["hinge"]
    n = gp.segment_count(s["length"], s.get("segments"))
    seg = s["length"] / n
    quads, _ = load_model(ship)
    tris = _tris(quads)
    hw = s["width"] / 2 + 0.1
    worst, rows = 0.0, []
    for dy in np.arange(-STOW_DROP + 0.1, -STOW_DROP - seg - 0.12, -0.08):
        m = -9.0
        for z in np.linspace(hz - hw, hz + hw, 17):
            t = raycast(tris, (o * 40, hy + dy, z), (-o, 0, 0))
            if len(t):
                m = max(m, o * (o * 40 - o * t[0]) - o * hx)
        rows.append((round(float(dy), 2), round(m, 3)))
        worst = max(worst, m)
    return worst, rows


def load_spec(ship):
    with open(os.path.join(ASSETS, "gangplanks", ship + ".json")) as f:
        return json.load(f)


# --------------------------------------------------------------------------------------------- per vessel
def place(ship, side, z, width, hy, hx, deck, inner, length, style, angles, max_drop=None, lever=None, lever_end=1,
          step=True, rail_gap=True, **extra):
    """A plank centred at z on `side`, hinged on the hull's outer face at |x| = hx and height hy (the top of the
    rail / bulwark); `deck` is the deck height inboard and `inner` |x| of the inner face of the bulwark there.
    The step box (stairs of <= 0.45, see core/Gangplank.stairBoxes) fills from the deck to the hinge height, its outboard
    face against the bulwark; the lever stands on the deck along the bulwark just beyond one end of the stairs
    (lever_end +1: towards the bow, -1: towards the stern) unless given."""
    o = 1 if side == "port" else -1
    s = dict(side=side, hinge=[o * hx, hy, z], width=width, length=length, style=style, angles=list(angles))
    rise = hy - deck
    n = max(1, int(math.ceil(rise / STAIR_RISE - 1e-9)))
    depth = max(0.5, 0.45 * n)
    if step and rise > 0.05:
        s["step"] = [o * (inner + 0.04), deck, z - width / 2, o * (inner - depth), hy, z + width / 2]
    if rail_gap:
        s["rail_gap"] = [z - width / 2, z + width / 2]
    s["max_drop"] = max_drop if max_drop is not None else math.floor(length * math.sin(math.radians(angles[1])) * 100) / 100
    s["lever"] = lever if lever is not None else [o * (inner - 0.45), deck, z + lever_end * (width / 2 + 0.45)]
    s.update(extra)
    SPECS[ship] = s


# Ships (hull walls from ShipGeometry: outer face ~ halfWidth, inner face halfWidth - 0.2; deck and rail from HullShape)
# galley: eight oars a side under the rail (28 deg down from rail - 0.32): the plank sits on the rail and its slope stays
# under 25 deg so it passes over them; between the benches at z 1.6 and 4.8, aft of the bow lantern.
place("galley", "starboard", 3.2, 2.0, 1.63, 2.48, 0.45, 2.24, 3.5, "wood", (-25, 25), lever_end=1,
      lever=[-1.8, 0.45, 4.42])
# galleon: dark wood with iron; between the deck guns at z -6 and -3 (their carriages leave a 2 block gap), clear of
# the main shrouds (z -0.7..2.8) and of the quarterdeck stairs (z < -6).
place("galleon", "starboard", -4.5, 2.0, 2.22, 4.39, 1.0, 4.27, 5.5, "dark_wood", (-20, 38), lever_end=1,
      lever=[-2.55, 1.0, -5.25])
# warship: between the deck guns at z -7 and -3.5 (y 5.4), clear of the main shrouds and the quarterdeck stairs; the
# deck is 5.6 above the water, hence the long plank.
place("warship", "starboard", -5.25, 2.4, 5.83, 6.33, 4.5, 6.25, 9.0, "dark_wood", (-15, 42), lever_end=1,
      lever=[-4.6, 4.5, -6.25])
# medieval galley: the shields cover the whole rail (top 2.15): the plank lies on top of the shield rims; oar ports are
# low (0.75), far under it. Between the mast (0.6) and the bench at 3.6.
place("medieval_galley", "starboard", 1.8, 2.0, 2.15, 2.6, 0.45, 2.26, 4.0, "wood", (-25, 30), lever_end=-1, segments=4,
      lever=[-1.6, 0.45, 0.45])
# steam paddleboat: steel; on the open railing aft of the deckhouse and of the paddle box, beside the stern gun's
# barbette (x +-0.95, z -8.55..-6.65).
place("steam_paddleboat", "starboard", -6.7, 2.0, 3.37, 3.6, 2.4, 3.52, 5.5, "steel", (-20, 40), lever_end=1,
      lever=[-2.2, 2.4, -5.3])
# elven sailboat: light elven wood; between the deck hatches (z -2 and -5.5), aft of the shrouds.
place("elven_sailboat", "starboard", -3.8, 2.2, 1.94, 2.8, 0.6, 2.66, 4.0, "elven", (-25, 35), lever_end=1,
      lever=[-1.05, 0.6, -2.55])
# nautilus (surfaced): from the edge of the casing platform (walking floor at 9.0, |x| <= 2), forward of the railing
# and of the salon shutters (z < 7), aft of the tower; the platform is 9 blocks above the water: a long plank; its
# first step box spans the casing's rounded edge, no stairs.
place("nautilus", "starboard", 9.0, 3.0, 9.0, 2.3, 9.0, 2.0, 12.0, "copper", (-10, 46), step=False, rail_gap=False,
      lever=[-1.4, 9.0, 7.1])
# old corsair: worn pirate planks; amidships between the two masts' shrouds (z -9..-5 and 4.5..8.5); the bulwark of the
# interior grid tops at 6.0 (deck 4.5).
place("old_corsair", "starboard", 0.0, 3.0, 6.0, 4.7, 4.5, 4.0, 8.0, "worn", (-15, 42), rail_gap=False, lever_end=1,
      lever=[-3.5, 4.5, 1.95])
# blue frigate: between the main and fore shrouds; bulwark top 7.0 over the deck at 5.5; the open hatch is on the port side.
place("blue_frigate", "starboard", 1.0, 3.0, 7.55, 4.6, 5.5, 4.0, 10.0, "dark_wood", (-15, 42), rail_gap=False, lever_end=1,
      lever=[-3.5, 5.5, 2.95])
# Large airships (max_drop: the reach to a landing platform under the gallery)
# crystal airship: on the waist between the side benches (z -5..-4 and 3..4); deck 0, bulwark 1.0 (grid).
place("crystal_airship", "starboard", -0.5, 3.5, 1.13, 6.03, 0.0, 5.5, 5.5, "crystal", (-25, 45), rail_gap=False, lever_end=-1,
      lever=[-5.0, 0.0, -2.8])
# sky leviathan: waist (deck 0, bulwark 1.0), aft of the deck furniture, forward of the quarterdeck stairs.
place("sky_leviathan", "starboard", -1.5, 3.0, 1.14, 5.02, 0.0, 4.5, 5.5, "dark_wood", (-25, 45), rail_gap=False, lever_end=1,
      lever=[-4.05, 0.0, 0.45])
# dragon junk: jade and red lacquer; on the waist between the bulwark gaps at z 6.75 and 11.25, aft of the raked mast.
place("dragon_junk", "starboard", 9.5, 3.0, 1.14, 3.98, 0.0, 3.5, 5.5, "jade", (-25, 45), rail_gap=False, lever_end=-1,
      lever=[-3.1, 0.0, 7.2])


# Stowed pack (1.23.1): the outermost surface of the model under each hinge, over the pack's height and width (`stow`),
# or the hull shape's outer face (core/Gangplank.hullStandoff) if further out, rounded up. The galley's is its hull
# side: two of its oars cross the pack's span (they already pass under the deployed plank and through its stairs).
STOW_OFFSET = {"galley": 0.10, "galleon": 0.24, "warship": 0.22, "medieval_galley": 0.07, "steam_paddleboat": 0.29,
               "elven_sailboat": 0.18, "old_corsair": 0.30, "blue_frigate": 0.55, "crystal_airship": 0.11,
               "sky_leviathan": 0.17, "dragon_junk": 0.35}
for _ship, _off in STOW_OFFSET.items():
    SPECS[_ship]["stow_offset"] = _off


def main():
    args = sys.argv[1:]
    cmd = args[0] if args else "all"
    if cmd in ("specs", "all"):
        write_specs(args[1:] or None)
    if cmd in ("models", "all"):
        make_models(args[1:] or None)
    if cmd == "probe":
        ys = [float(v) for v in args[2].split(",")]
        zs = [float(v) for v in args[3].split(",")]
        probe(args[1], [(y, z) for y in ys for z in zs])
    if cmd == "deck":
        xs = [float(v) for v in args[2].split(",")]
        zs = [float(v) for v in args[3].split(",")]
        deck_probe(args[1], [(x, z) for x in xs for z in zs])
    if cmd == "sheet":
        sheet(args[1], args[2:] or list(SPECS))
    if cmd == "single":
        for ship in args[2:]:
            single(ship, args[1])
    if cmd == "stow":
        for ship in args[1:] or list(SPECS):
            worst, rows = stow_probe(ship)
            print("%s: model surface up to %.3f outboard of the hinge under it (spec stow_offset %s)" % (
                ship, worst, (SPECS.get(ship) or load_spec(ship)).get("stow_offset")), flush=True)
            print("   ", " ".join("%.2f:%.2f" % r for r in rows), flush=True)


if __name__ == "__main__":
    main()
