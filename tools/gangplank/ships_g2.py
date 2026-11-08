"""Gangplanks (passerelles) of the ships and large airships other than the two reference vessels (trade_sloop and
steampunk_airship, see gangplanklib.py / core/Gangplank.java): their specs, plank models and verification renders.

    python3 tools/gangplank/ships_g2.py specs            # writes assets/medievalships/gangplanks/<id>.json
    python3 tools/gangplank/ships_g2.py models           # gangplank_<id>.bbmodel (+ the levers of the styles used)
    python3 tools/gangplank/ships_g2.py probe <id> ys zs # outer face of the hull model at (y, z) on both sides
    python3 tools/gangplank/ships_g2.py deck <id> xs zs  # model surfaces under (x, z) (TOP=<y> to start lower)
    python3 tools/gangplank/ships_g2.py sheet <out.png> [ids...]   # contact sheet: one row per vessel (before / after)
    python3 tools/gangplank/ships_g2.py single <dir> ids...        # the 640x480 views of each vessel
    python3 tools/gangplank/ships_g2.py stow [ids...]              # model surface under the 1.23.1 accordion pack
    python3 tools/gangplank/ships_g2.py compact [ids...]           # model surface under the compact pack + flush fit
    python3 tools/gangplank/ships_g2.py camo [ids...]              # hull colours behind the pack (gangplanklib.CAMO)
    BEFORE=<dir> python3 tools/gangplank/ships_g2.py sheet <out.png>   # with <dir>/<id>_before[_close].png (1.23.1)

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
- stowed (1.23.2), the wings fold over the centre strip and the segments slide into segment 0: a flat pack half the
  plank wide and one segment high, hanging stow_drop under the hinge, flat against the hull side: stow_offset is the
  outermost surface of the ship model over the pack's footprint at its top and stow_tilt the lean that follows the side
  (`compact` measures and fits them; core/Gangplank.fold keeps the pack STOW_CLEARANCE beyond); segments and stow_drop
  put the pack on a smooth stretch (COMPACT); its outer face is painted with the hull's colours there (`camo`).
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
                  "max_drop", "chain_anchor", "stowed_angle", "handrails", "segments", "stow_offset", "stow_drop", "stow_tilt"):
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


# ---- the compact folding (1.23.2), as core/Gangplank.java (fold, foldPose, plankPoint, railPoint)
STOW_CLEARANCE, STOW_DROP, HANG, RAISE = 0.02, 0.12, 90.0, 20.0
UNLOCK, SETTLE = 0.1, 0.12
LIFT_END, WING_START, WING_END, TELE_START, TELE_END, LOWER_START, RAIL_START = 0.36, 0.30, 0.46, 0.47, 0.74, 0.66, 0.74
NEST_DROP, NEST_SHRINK, NEST_RAMP, RAIL_LOW = 0.04, 0.985, 0.15, 0.1


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
    hang = HANG - s.get("stow_tilt", 0.0)
    r = math.radians(hang)
    return dict(n=n, seg=seg, standoff=standoff, hang=hang, offX=standoff + gp.STRIP_DEPTH * math.sin(r),
                offY=-s.get("stow_drop", STOW_DROP) + gp.STRIP_DEPTH * math.cos(r))


def fold_pose(f, p, target):
    """core/Gangplank.foldPose: dict(a, cx, cy, wing, rail, chain, ext=[e_0..e_n-1])."""
    n = f["n"]
    raised = min(target, 0.0) - RAISE
    swing_end = 1.0 - SETTLE
    hang = f["hang"]
    if p <= 0:
        a0, g = hang, 1.0
    elif p < UNLOCK:
        a0, g = hang - 3.0 * math.sin(math.pi * p / UNLOCK), 1.0
    elif p < LIFT_END:
        e = _ease((p - UNLOCK) / (LIFT_END - UNLOCK))
        a0, g = hang + (raised - hang) * e, 1 - e
    elif p < LOWER_START:
        a0, g = raised, 0.0
    elif p < swing_end:
        a0, g = raised + (target - raised) * _ease((p - LOWER_START) / (swing_end - LOWER_START)), 0.0
    elif p < 1:
        r = (p - swing_end) / SETTLE
        a0, g = target - 1.5 * math.sin(math.pi * r) * (1 - r * 0.5), 0.0
    else:
        a0, g = target, 0.0
    done = p >= 1
    wing = 0.0 if done else 180.0 * (1.0 - _ease((p - WING_START) / (WING_END - WING_START)))
    rail = 1.0 if done else _ease((p - RAIL_START) / (swing_end - RAIL_START))
    chain = 1.0 if done else _ease(p / LIFT_END)
    E = (n - 1) * (1.0 if done else _ease((p - TELE_START) / (TELE_END - TELE_START)))
    ext = [1.0] + [max(0.0, min(1.0, E - (k - 1))) for k in range(1, n)]
    return dict(a=a0, cx=g * f["offX"], cy=g * f["offY"], wing=wing, rail=rail, chain=chain, ext=ext)


def visible(pose, k, rail=False):
    """core/Gangplank.visible / railVisible: a nested segment is inside the previous one (not drawn); its handrails
    show once it is fully out."""
    e = pose["ext"][k]
    return e >= 1.0 if rail else (k == 0 or e > 0.0)


def fold_point(s, f, pose, k, part, p):
    """core/Gangplank.plankPoint: ship-local point of model point p of segment k, part 0 (strip) or -1 / +1 (wing)."""
    import gangplanklib as gp
    u, v, w = float(p[0]), float(p[1]), float(p[2])
    if part:
        pz = part * (s["width"] / 4 + gp.WING_GAP)
        ph = math.radians(pose["wing"])
        c, sn = math.cos(ph), math.sin(ph)
        dv, dw = v - gp.WING_PIVOT, w - pz
        w = pz + dw * c - part * dv * sn
        v = gp.WING_PIVOT + part * dw * sn + dv * c
    ext = pose["ext"]
    u -= f["seg"] * sum(1.0 - ext[j] for j in range(1, k + 1))
    e = ext[k]
    if k > 0 and e < 1.0:
        r = min(1.0, (1.0 - e) / NEST_RAMP)
        v -= NEST_DROP * r
        w *= 1.0 - (1.0 - NEST_SHRINK) * r
    o = 1 if s["side"] == "port" else -1
    hx, hy, hz = s["hinge"]
    a = math.radians(pose["a"])
    c, sn = math.cos(a), math.sin(a)
    return np.array([hx + o * (pose["cx"] + u * c + v * sn), hy + pose["cy"] - u * sn + v * c, hz + o * w])


def rail_point(rise, p):
    """core/Gangplank.railPoint: the handrail's posts telescope (scaled along v from the walking surface)."""
    k = RAIL_LOW + (1.0 - RAIL_LOW) * rise
    return np.array([p[0], p[1] * k, p[2]])


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
    """{"seg_k": quads, "wing_k_s": quads, "rail_k_s": quads} of a compact folding plank model (1.23.2), and its
    texture: the strip, each wing without its handrail, each handrail."""
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
            parts["wing_%d_%d" % (k, side)] = part_quads(model, "wing_%d_%d" % (k, side))
            parts["rail_%d_%d" % (k, side)] = part_quads(model, "rail_%d_%d" % (k, side), children=True)
        k += 1
    return parts, tex


def folded_quads(s, f, parts, pose, tex_offset):
    """The plank's quads in a fold pose (ship-local), nested segments and their handrails left out as the mod does."""
    out = []
    for name, quads in parts.items():
        bits = name.split("_")
        k = int(bits[1])
        is_rail = bits[0] == "rail"
        if not visible(pose, k, rail=is_rail):
            continue
        part = 0 if bits[0] == "seg" else (1 if bits[2] == "1" else -1)
        for corners, uvs, glow, ti in quads:
            pts = []
            for p in corners:
                if is_rail:
                    p = rail_point(pose["rail"], p)
                pts.append(fold_point(s, f, pose, k, part, p))
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


POST, POST_HEIGHT, POST_LOW, EYE_INSET, STAIR_RISE = 0.13, 2.5, 0.08, 0.16, 0.45   # as GangplankRenderer / core/Gangplank.java


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


def chain_quads(s, tip, tex_offset, deployed, chain=1.0):
    """Stand-in for what GangplankRenderer draws besides the models: the two chains / ropes (from the chain anchor, or
    from a small gallows post at each end of the hinge, which telescopes up from the rail as the plank lifts) to tip(w)
    (the plank's outer corner eyes), paid out by `chain` (0: retracted, nothing drawn), and, while the plank is out,
    the inboard stairs."""
    import gangplanklib as gp
    o = 1 if s["side"] == "port" else -1
    cord, rail, metal = (gp.REGIONS["%s_%s" % (s["style"], k)] for k in ("cord", "rail", "metal"))
    plank_top, board = gp.REGIONS["%s_plank" % s["style"]], gp.REGIONS["%s_board" % s["style"]]
    out = []
    hx, hy, hz = s["hinge"]
    ph = POST_LOW + (POST_HEIGHT - POST_LOW) * chain
    for side in (-1, 1):
        w = side * (s["width"] / 2 - EYE_INSET)
        if s.get("chain_anchor"):
            ax, ay, az = s["chain_anchor"]
            a = np.array([ax, ay, az + o * w])
        else:
            px, pz = hx - o * 0.12, hz + o * side * (s["width"] / 2 + 0.12)
            out += _box_quads(px - POST / 2, hy - 0.1, pz - POST / 2, px + POST / 2, hy + ph, pz + POST / 2, rail, tex_offset)
            out += _box_quads(px - 0.1, hy + ph - 0.2, pz - 0.1, px + 0.1, hy + ph + 0.04, pz + 0.1, metal, tex_offset)
            a = np.array([px, hy + ph - 0.08, pz])
        if chain <= 0:
            continue
        b = a + (tip(w) - a) * chain
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
    pose = fold_pose(f, p, target)
    k = f["n"] - 1
    side = lambda w: 1 if w > 0 else -1  # noqa: E731
    tip = lambda w: fold_point(s, f, pose, k, side(w), (s["length"] - 0.25, 0.05, w))  # noqa: E731
    return folded_quads(s, f, parts, pose, off) + lever_quads(s, lever, off) + chain_quads(s, tip, off, p > 0, pose["chain"])


def render_views(ship, s, ship_mesh=None, size=(640, 480), before_dir=None):
    """[(title, image)]: (with before_dir, the 1.23.1 accordion pack rendered beforehand with the same cameras:
    <ship>_before_close.png / <ship>_before.png), the compact pack stowed close up from outboard and in the 3/4 view,
    the plank telescoping out (p = 0.6), deployed at 20 degrees. Ship-local space, centred on the hinge."""
    import preview
    from PIL import Image, ImageDraw
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
    pack = hinge + np.array([o * 1.0, -0.8, 0])
    eye_c = pack + np.array([o * 4.5, 1.6, 3.2])
    views = []

    def before(name, title):
        path = os.path.join(before_dir, "%s_%s.png" % (ship, name)) if before_dir else None
        if path and os.path.exists(path):
            views.append((title, Image.open(path).convert("RGB")))

    stowed = folded_scene(ship, s, parts, lever, off, 0.0, 20.0)
    before("before_close", None)
    views.append(("apres (1.23.2) : paquet", preview.render(quads + stowed, textures, W, H, eye=tuple(eye_c), target=tuple(pack), fov=50)))
    before("before", None)
    views.append(("apres (1.23.2) : rangee", preview.render(quads + stowed, textures, W, H, eye=tuple(eye34), target=tgt_old, fov=55)))
    tgt34 = hinge + np.array([o * 0.35 * L, -0.25 * L, 0])
    mid = folded_scene(ship, s, parts, lever, off, 0.6, 20.0)
    views.append(("depliage (mi-course)", preview.render(quads + mid, textures, W, H, eye=tuple(eye34), target=tuple(tgt34), fov=55)))
    deployed = folded_scene(ship, s, parts, lever, off, 1.0, 20.0)
    views.append(("deployee 20 deg", preview.render(quads + deployed, textures, W, H, eye=tuple(eye34), target=tuple(tgt34), fov=55)))
    for title, im in views:
        if title:
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


def sheet(out, ids, before_dir=None):
    from PIL import Image, ImageDraw
    cw, ch = 320, 240
    rows = []
    for ship in ids:
        s = SPECS[ship] if ship in SPECS else load_spec(ship)
        views = render_views(ship, s, before_dir=before_dir)
        for i, (title, im) in enumerate(views):
            if title:   # the 640 x 480 views rendered here (the "before" ones are files already)
                im.save(os.path.join(os.path.dirname(os.path.abspath(out)), "%s_view%d.png" % (ship, i)))
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


def single(ship, outdir, before_dir=None, extra=()):
    """The 640x480 views of one vessel (and the stowed / moving close-ups at the progress values in `extra`)."""
    s = SPECS[ship] if ship in SPECS else load_spec(ship)
    for i, (_t, im) in enumerate(render_views(ship, s, before_dir=before_dir)):
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


def hull_colours(ship, s=None):
    """Camouflage of the stowed pack (1.23.2): the colours of the ship model's outer surface where the pack lies (the
    texels hit by rays from outboard over the pack's footprint) and of the band just under the hinge (the rail cap /
    moulding, the trim). Returns (skin rgb, dark rgb, trim rgb) as hex strings, for gangplanklib.CAMO."""
    import gangplanklib as gp
    s = s or (SPECS[ship] if ship in SPECS else load_spec(ship))
    o = 1 if s["side"] == "port" else -1
    hx, hy, hz = s["hinge"]
    with open(os.path.join(MODELS, ship + ".bbmodel")) as f:
        res = json.load(f).get("resolution", {"width": 16, "height": 16})
    quads, tex = load_model(ship)
    a, b, c = _tris(quads)
    tri_q = np.repeat(np.arange(len(quads)), 2)
    tri_k = np.tile([1, 2], len(quads))   # second corner of each triangle (p0, p1, p2) / (p0, p2, p3)

    def texel(origin, d):
        e1, e2 = b - a, c - a
        p = np.cross(d, e2)
        det = np.einsum("ij,ij->i", e1, p)
        ok = np.abs(det) > 1e-12
        inv = np.where(ok, 1.0 / np.where(ok, det, 1), 0)
        sv = np.asarray(origin, float) - a
        u = np.einsum("ij,ij->i", sv, p) * inv
        q = np.cross(sv, e1)
        v = (q @ d) * inv
        t = np.einsum("ij,ij->i", e2, q) * inv
        hit = ok & (u >= 0) & (v >= 0) & (u + v <= 1) & (t > 0)
        if not hit.any():
            return None
        i = np.where(hit)[0][np.argmin(t[hit])]
        corners, uvs, _g, ti = quads[tri_q[i]]
        k = tri_k[i]
        uv0, uv1, uv2 = np.array(uvs[0]), np.array(uvs[k]), np.array(uvs[k + 1])
        uvp = uv0 + (uv1 - uv0) * u[i] + (uv2 - uv0) * v[i]
        img = tex[ti]
        x = int(np.clip(uvp[0] * img.shape[1] / res["width"], 0, img.shape[1] - 1))
        y = int(np.clip(uvp[1] * img.shape[0] / res["height"], 0, img.shape[0] - 1))
        px = img[y, x]
        return None if px[3] < 128 else px[:3]

    n = gp.segment_count(s["length"], s.get("segments"))
    seg = s["length"] / n
    hw = gp.strip_width(s["width"]) / 2
    d = np.array([-o, 0.0, 0.0])
    skin = []
    for dy in np.linspace(-STOW_DROP - 0.05, -STOW_DROP - seg + 0.05, 7):
        for z in np.linspace(hz - hw, hz + hw, 7):
            px = texel((o * 40, hy + dy, z), d)
            if px is not None:
                skin.append(px)
    trim = []
    for dy in (-0.03, -0.07):
        for z in np.linspace(hz - hw, hz + hw, 9):
            px = texel((o * 40, hy + dy, z), d)
            if px is not None:
                trim.append(px)
    skin = np.array(skin) if skin else np.array([[110, 80, 50]])
    trim = np.array(trim) if trim else skin
    base = np.median(skin, axis=0)
    dark = np.percentile(skin, 15, axis=0) * 0.85
    tr = np.median(trim, axis=0)
    # a trim too close to the skin reads as nothing: take the most contrasting quarter of the band then
    if np.linalg.norm(tr - base) < 40:
        dist = np.linalg.norm(trim - base, axis=1)
        far = trim[dist >= np.percentile(dist, 75)]
        tr = np.median(far, axis=0) if len(far) else tr
    hexs = lambda v: "%02x%02x%02x" % tuple(int(round(max(0, min(255, x)))) for x in v)  # noqa: E731
    return hexs(base), hexs(dark), hexs(tr)


def fit_stow(rows, drop, tilts=range(-20, 31, 1)):
    """stow_offset and stow_tilt for the probe rows of compact_probe: the tilt (degrees, bottom outboard) whose flat pack
    leaves the smallest largest gap to the model's surface (negative: leaning in along a tumblehome), its inner face never inside it. Returns (offset, tilt, gap)."""
    best = None
    for t in tilts:
        k = math.tan(math.radians(t))
        off = max(m - max(0.0, -drop - y) * k for y, m in rows)
        gap = max(off + max(0.0, -drop - y) * k - m for y, m in rows)
        if best is None or gap < best[2] - 0.01:
            best = (off, t, gap)
    return best


def compact_probe(ship, s=None):
    """Outermost surface of the ship model over the compact stowed pack's footprint (1.23.2: the centre strip's width,
    one segment high under STOW_DROP), outboard of the hinge line: the spec's stow_offset. Returns (max, rows)."""
    import gangplanklib as gp
    s = s or (SPECS[ship] if ship in SPECS else load_spec(ship))
    o = 1 if s["side"] == "port" else -1
    hx, hy, hz = s["hinge"]
    n = gp.segment_count(s["length"], s.get("segments"))
    seg = s["length"] / n
    quads, _ = load_model(ship)
    tris = _tris(quads)
    hw = gp.strip_width(s["width"]) / 2 + gp.WING_GAP + gp.WING_KNUCKLE_R + 0.02
    drop = s.get("stow_drop", STOW_DROP)
    worst, rows = -9.0, []
    for dy in np.arange(-drop + 0.04, -drop - seg - 0.04, -0.04):
        m = -9.0
        for z in np.linspace(hz - hw, hz + hw, 13):
            t = raycast(tris, (o * 40, hy + dy, z), (-o, 0, 0))
            if len(t):
                m = max(m, o * (o * 40 - o * t[0]) - o * hx)
        rows.append((round(float(dy), 2), round(m, 3)))
        worst = max(worst, m)
    return worst, rows


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
# royal lion ship (lot 2): on the waist between the main and fore shrouds, starboard (the hold's companionway is on the
# port side); the bulwark of the grid tops at 6.0 over the deck at 4.5, the gold cap rail at 6.36: hinge over it.
place("royal_lion_ship", "starboard", 3.0, 3.0, 6.4, 5.47, 4.5, 5.0, 9.0, "dark_wood", (-15, 42), rail_gap=False, lever_end=1)
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


# Compact stowed pack (1.23.2): the telescoping segments (pack height) and the pack's drop under the hinge are chosen
# so that the pack lies on a flat stretch of the side, clear of wales and bands (warship: under the rail moulding;
# galleon / paddleboat: above the wale; elven sailboat: below the step of its sheer strake; junk: under the rail cap);
# stow_offset / stow_tilt are the flush fit of `compact` (the outermost model surface over the pack's footprint at its
# top, and the lean that follows a flaring side), rounded up to 0.01.
COMPACT = {
    #                   segments, stow_drop, stow_offset, stow_tilt
    "galley":           (None, 0.18, 0.05, -3),
    "galleon":          (11, 0.36, 0.04, 4),
    "warship":          (None, 0.36, 0.08, 0),
    "medieval_galley":  (None, None, 0.05, 0),
    "steam_paddleboat": (10, None, 0.01, 0),
    "elven_sailboat":   (None, 0.46, 0.13, 0),
    "old_corsair":      (11, None, -0.10, 0),
    "blue_frigate":     (None, None, -0.04, 9),
    "crystal_airship":  (None, None, 0.10, 0),
    "sky_leviathan":    (None, None, 0.11, 0),
    "dragon_junk":      (None, 0.24, 0.05, 0),
    "royal_lion_ship":  (16, 1.0, 0.14, 13),
}
for _ship, (_n, _drop, _off, _tilt) in COMPACT.items():
    _s = SPECS[_ship]
    _s.pop("segments", None)
    if _n:
        _s["segments"] = _n
    if _drop is not None:
        _s["stow_drop"] = _drop
    _s["stow_offset"] = _off
    if _tilt:
        _s["stow_tilt"] = _tilt

# every equipped vessel (the steampunk airship's spec is written by hand, see the module doc)
EQUIPPED = [s for s in SPECS if s not in NOT_EQUIPPED] + ["steampunk_airship"]


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
        sheet(args[1], args[2:] or EQUIPPED, before_dir=os.environ.get("BEFORE"))
    if cmd == "single":
        for ship in args[2:]:
            single(ship, args[1], before_dir=os.environ.get("BEFORE"))
    if cmd == "camo":
        for ship in args[1:] or EQUIPPED:
            print("    %r: %r," % (ship, hull_colours(ship)), flush=True)
    if cmd == "compact":
        for ship in args[1:] or EQUIPPED:
            worst, rows = compact_probe(ship)
            sp = SPECS.get(ship) or load_spec(ship)
            off, tilt, gap = fit_stow(rows, sp.get("stow_drop", STOW_DROP))
            print("%s: model surface up to %.3f outboard of the hinge over the compact pack (spec stow_offset %s); "
                  "flush fit: stow_offset %.3f stow_tilt %d (largest gap %.3f, straight %.3f)" % (
                      ship, worst, sp.get("stow_offset"), off, tilt, gap, fit_stow(rows, sp.get("stow_drop", STOW_DROP), [0])[2]),
                  flush=True)
            print("   ", " ".join("%.2f:%.2f" % r for r in rows), flush=True)
    if cmd == "stow":
        for ship in args[1:] or list(SPECS):
            worst, rows = stow_probe(ship)
            print("%s: model surface up to %.3f outboard of the hinge under it (spec stow_offset %s)" % (
                ship, worst, (SPECS.get(ship) or load_spec(ship)).get("stow_offset")), flush=True)
            print("   ", " ".join("%.2f:%.2f" % r for r in rows), flush=True)


if __name__ == "__main__":
    main()
