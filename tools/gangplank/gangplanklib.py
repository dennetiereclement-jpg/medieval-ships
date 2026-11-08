"""Boarding gangplanks (passerelles) of the ships and large airships: the plank model of each vessel, the deck lever
of each style, and their shared atlas textures/entity/gangplank.png.

    import gangplanklib as gp
    gp.make_plank("trade_sloop", 2.0, 4.0, "worn")     # -> models/entity/gangplank_trade_sloop.bbmodel
    gp.make_lever("worn")                              # -> models/entity/gangplank_lever_worn.bbmodel
    gp.atlas()                                         # -> textures/entity/gangplank.png (also done by the two above)

    python3 tools/gangplank/gangplanklib.py            # every lever, the atlas, and the plank of each
                                                       # assets/medievalships/gangplanks/<ship>.json found

Model frame (model-local blocks, the frame BbModel.render emits, x = -bbX/16, y = bbY/16, z = -bbZ/16):
- the plank: hinge line along the z axis through the origin, the plank extending along +x when horizontal, its walking
  (top) surface at y = 0, centred on z (z in [-width/2, width/2]), drawn straight; boards, cleats, side stringers under
  the boards, iron (or copper...) side straps, hinge knuckles at x = 0, posts and handrails, a bevelled tip at
  x = length, eyes for the support chains at the outer corners (x = length - 0.25, z = +-(width/2 - 0.08)). It folds
  like an accordion: one bone "seg_<k>" per segment (segment_count, origin (k s, 0, 0)), side hinge plates and knuckles
  at each joint, the handrails of each segment in its bones "rail_<k>_0" / "rail_<k>_1". No animation: the mod places
  each segment (and folds its handrails) itself (core/Gangplank.java documents the folding and how the model frame maps
  to the ship).
- the lever: its base on the deck at the origin (y = 0 = the deck surface), a bone "handle" pivoting at
  (0, PIVOT_Y, 0) that the mod tilts about the model's z axis (positive = towards +x); the lever faces +x (the
  side the handle is pulled towards when deploying).

Styles (one region set each in the atlas): wood, dark_wood, worn, elven, copper, crystal, jade, steel.
"""
import math
import os
import random
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(HERE, "..")
ROOT = os.path.abspath(os.path.join(TOOLS, ".."))
sys.path.insert(0, TOOLS)
sys.path.insert(0, HERE)
import generate_galley as gg  # noqa: E402
import generate_galleon as gn  # noqa: E402
from galley_texture import _rgb, _jitter, _scale, _mix, fine_wood, hammered_iron, twisted_rope, end_grain, polished_metal  # noqa: E402

v3, norm, Bone, add_cube, beam = gg.v3, gg.norm, gg.Bone, gg.add_cube, gg.beam
EYE = np.eye(3)
UP = v3(0, 1, 0)
ASSETS = os.path.join(ROOT, "src/main/resources/assets/medievalships")
TEX_NAME = "gangplank.png"
SIZE = 256
STYLES = ("wood", "dark_wood", "worn", "elven", "copper", "crystal", "jade", "steel")
PIVOT_Y = 0.16
BOARD_TH = 0.09
STRINGER_H = 0.16

# per style: a 128 x 32 cell of the atlas; inside a cell: (u, v, w, h)
_CELL = {"plank": (0, 0, 64, 16), "board": (0, 16, 64, 16), "rail": (64, 0, 32, 16), "metal": (96, 0, 16, 16),
         "cord": (112, 0, 16, 16), "end": (64, 16, 16, 16), "accent": (80, 16, 16, 16), "handle": (96, 16, 16, 16),
         "knob": (112, 16, 16, 16)}
REGIONS = {}
for _i, _s in enumerate(STYLES):
    _ox, _oy = (_i % 2) * 128, (_i // 2) * 32
    for _k, (_u, _v, _w, _h) in _CELL.items():
        REGIONS["%s_%s" % (_s, _k)] = (_ox + _u, _oy + _v, _w, _h)

# style -> colours and options
PALETTE = {
    #            plank      plank dark  rail       metal      cord (light, dark)        accent     rope handrail, chain
    "wood":      ("b08452", "5e4022", "8e6a40", "3c3c40", ("c9ad7a", "6e5634"), "c9a24a", True, False),
    "dark_wood": ("6e4c2c", "2e1c0e", "4e3420", "35353a", ("b89a68", "5e4626"), "c9a24a", False, True),
    "worn":      ("8a7a62", "4a3e2e", "6e5e48", "5a3e2c", ("a89470", "564630"), "7a5a3a", True, False),
    "elven":     ("d8c8a0", "8a7650", "c8b088", "b8b8c8", ("e0d0a8", "8a7a58"), "d8b048", False, False),
    "copper":    ("6e4c2c", "2e1c0e", "b06a38", "b87333", ("8a8a90", "3a3a40"), "d8a848", False, True),
    "crystal":   ("e8e4f0", "8a86a8", "d0d4e8", "c8ccd8", ("b8bccc", "5a5e70"), "7ad0f0", False, True),
    "jade":      ("8f2b22", "4a1210", "3e8a6a", "c9a24a", ("c9a24a", "6a5020"), "4fb08a", False, False),
    "steel":     ("7a7e86", "3a3e46", "5a5e66", "4a4e56", ("8a8e96", "3a3e46"), "c8a040", False, True),
}


def _style(style):
    if style not in PALETTE:
        raise ValueError("unknown gangplank style %r (one of %s)" % (style, ", ".join(STYLES)))
    return PALETTE[style]


def R(style, part):
    return "%s_%s" % (style, part)


# ---------------------------------------------------------------- atlas
def _chain(img, region, light, dark, rng):
    """Links of a chain along u: alternating open ovals and edge-on links on a transparent background."""
    u, v, w, h = region
    px = img.load()
    for y in range(h):
        for x in range(w):
            px[u + x, v + y] = (0, 0, 0, 0)
    for x in range(w):
        k = x % 8
        for y in range(h):
            cy = abs(y + 0.5 - h / 2) / (h / 2)
            if k < 5:   # open link seen flat: a ring
                ex = abs(k - 2) / 2.5
                r = math.hypot(ex, cy)
                if 0.55 < r < 1.0:
                    c = _mix(light, dark, min(1.0, abs(cy)))
                    px[u + x, v + y] = _jitter(c, rng, 4) + (255,)
            else:       # link seen edge on: a bar
                if cy < 0.3:
                    px[u + x, v + y] = _jitter(_mix(light, dark, 0.3 + cy), rng, 4) + (255,)


def _rivets(img, region, base, rng, step=8):
    u, v, w, h = region
    px = img.load()
    for y in range(h):
        for x in range(w):
            k = 1.0 + 0.05 * math.sin(x * 0.3 + y * 0.5) + (0.08 if y in (0, h - 1) else 0.0)
            c = _scale(base, k)
            if (x % step == 3) and (y % 8 in (3, 4)):
                c = _scale(base, 1.35)
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def _wear(img, region, rng, n=10, dark=(60, 50, 40)):
    """Grey weathering streaks and a few cracks (the pirate's worn planks)."""
    u, v, w, h = region
    px = img.load()
    for _ in range(n):
        x0, y0 = rng.randrange(w), rng.randrange(h)
        L = rng.randint(4, 14)
        for t in range(L):
            x, y = (x0 + t) % w, min(h - 1, max(0, y0 + int(math.sin(t * 0.5) * 0.6)))
            r, g, b, a = px[u + x, v + y]
            px[u + x, v + y] = (int(r * 0.6 + dark[0] * 0.4), int(g * 0.6 + dark[1] * 0.4), int(b * 0.6 + dark[2] * 0.4), a)


def _crystal(img, region, base, rng):
    u, v, w, h = region
    px = img.load()
    for y in range(h):
        for x in range(w):
            t = 0.5 + 0.5 * math.sin((x + y) * 0.7) * math.cos((x - y) * 0.4)
            c = _mix(_scale(base, 0.7), _mix(base, (255, 255, 255), 0.6), t)
            px[u + x, v + y] = _jitter(c, rng, 3) + (255,)


def make_atlas(path):
    from PIL import Image
    rng = random.Random(1230)
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    for s in STYLES:
        plank, dark, rail, metal, (cl, cd), accent, rope_rail, chain = _style(s)
        P, D, Rl, Mt, A = _rgb(plank), _rgb(dark), _rgb(rail), _rgb(metal), _rgb(accent)
        if s == "steel":
            _rivets(img, REGIONS[R(s, "plank")], P, rng)
            _rivets(img, REGIONS[R(s, "board")], _scale(P, 0.9), rng, step=12)
        else:
            fine_wood(img, REGIONS[R(s, "plank")], P, D, 4, rng, joints=True, knots=0.2, grain=0.12, shade=0.07)
            fine_wood(img, REGIONS[R(s, "board")], _scale(P, 0.92), D, 16, rng, joints=False, knots=0.25, grain=0.12, shade=0.06)
        if s == "worn":
            _wear(img, REGIONS[R(s, "plank")], rng, n=18)
            _wear(img, REGIONS[R(s, "board")], rng, n=10)
        if s in ("copper", "crystal", "elven", "jade") and s != "jade":
            polished_metal(img, REGIONS[R(s, "rail")], [(0.0, _scale(Rl, 0.55)), (0.5, Rl), (0.85, _scale(Rl, 1.3)), (1.0, (250, 240, 210))], rng)
        elif s == "jade":
            _crystal(img, REGIONS[R(s, "rail")], Rl, rng)
        elif s == "steel":
            hammered_iron(img, REGIONS[R(s, "rail")], Rl, rng)
        else:
            fine_wood(img, REGIONS[R(s, "rail")], Rl, D, 16, rng, joints=False, knots=0.15, grain=0.1, shade=0.06)
        if s in ("copper", "jade", "elven"):
            polished_metal(img, REGIONS[R(s, "metal")], [(0.0, _scale(Mt, 0.5)), (0.5, Mt), (0.85, _scale(Mt, 1.3)), (1.0, (255, 245, 215))], rng)
        else:
            hammered_iron(img, REGIONS[R(s, "metal")], Mt, rng)
        if chain:
            _chain(img, REGIONS[R(s, "cord")], _rgb(cl), _rgb(cd), rng)
        else:
            twisted_rope(img, REGIONS[R(s, "cord")], _rgb(cl), _rgb(cd), rng)
        end_grain(img, REGIONS[R(s, "end")], _scale(P, 1.08), D, rng)
        if s == "crystal":
            _crystal(img, REGIONS[R(s, "accent")], A, rng)
        else:
            polished_metal(img, REGIONS[R(s, "accent")], [(0.0, _scale(A, 0.5)), (0.5, A), (0.85, _scale(A, 1.25)), (1.0, (255, 248, 220))], rng)
        fine_wood(img, REGIONS[R(s, "handle")], _scale(_rgb("8e6a40") if s != "steel" else Rl, 1.0), _rgb("3e2814"), 16, rng,
                  joints=False, knots=0.0, grain=0.1, shade=0.05, vertical=True)
        k = REGIONS[R(s, "knob")]
        polished_metal(img, k, [(0.0, (90, 20, 16)), (0.5, (160, 40, 30)), (0.9, (220, 90, 70)), (1.0, (250, 170, 150))], rng) \
            if s in ("wood", "dark_wood", "worn", "jade") else \
            polished_metal(img, k, [(0.0, _scale(A, 0.5)), (0.5, A), (1.0, (255, 248, 220))], rng)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)
    return path


_atlas_done = [False]


def atlas():
    """Writes textures/entity/gangplank.png (deterministic) and returns its path."""
    path = os.path.join(ASSETS, "textures/entity", TEX_NAME)
    if not _atlas_done[0]:
        make_atlas(path)
        _atlas_done[0] = True
    return path


# ---------------------------------------------------------------- model plumbing
_uuid_counter = [0]
_NAME = ["gangplank"]


def _new_uuid():
    import uuid
    _uuid_counter[0] += 1
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "medievalships/%s/%d" % (_NAME[0], _uuid_counter[0])))


def _setup(name):
    _NAME[0] = name
    _uuid_counter[0] = 0
    gg.new_uuid = _new_uuid
    gn.new_uuid = _new_uuid
    gn.REGIONS = {k: (0,) + r for k, r in REGIONS.items()}
    gn.SIZE = SIZE
    gg.REGIONS = dict(REGIONS)
    gg.SIZE = SIZE


def export(root, name, out=None):
    """Writes models/entity/<name>.bbmodel (or `out`) with the shared atlas; returns the model dict."""
    tex_path = atlas()
    with open(tex_path, "rb") as f:
        png = f.read()
    textures = [gn.texture_entry(TEX_NAME, SIZE, png, "entity", TEX_NAME)]
    textures[0]["id"] = "0"
    path = out or os.path.join(ASSETS, "models/entity/%s.bbmodel" % name)
    model = gn.export(root, [], textures, [path], name=name, visible_box=(8, 6, 0))
    print("%s: %d cubes -> %s" % (name, len(model["elements"]), os.path.relpath(path, ROOT)))
    return model


def _box(bone, name, x0, y0, z0, x1, y1, z1, region, **kw):
    add_cube(bone, name, ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), EYE, (abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)), region, **kw)


def _knuckle(bone, name, x, y, z0, z1, r, region):
    """A hinge knuckle (a short cylinder along z, two crossed square sections)."""
    c = ((z0 + z1) / 2)
    for k, a in enumerate((0.0, math.pi / 4)):
        Rz = gg.rz(a)
        add_cube(bone, "%s_%d" % (name, k), (x, y, c), Rz, (r * 1.7, r * 1.7, z1 - z0), region)


# ---------------------------------------------------------------- the plank
# Folding (accordion) geometry, as core/Gangplank.java (SEGMENT, FOLD_UNDER, FOLD_OVER, RAIL_PIVOT_V, RAIL_PIVOT_INSET)
SEGMENT = 1.6
MAX_SEGMENTS = 12
FOLD_UNDER = 0.27
FOLD_OVER = 0.135
RAIL_PIVOT_V = 0.075
RAIL_PIVOT_INSET = 0.04
HINGE_R = 0.055      # radius of the side knuckles of a joint between two segments
PLATE = 0.18         # length of a joint's side hinge plate along the plank


def segment_count(length, segments=None):
    """core/Gangplank.segments: the override, else ceil(length / SEGMENT), at least 2."""
    n = int(segments) if segments else int(math.ceil(length / SEGMENT - 1e-9))
    return max(2, min(MAX_SEGMENTS, n))


def make_plank(ship_id, width, length, style, handrails=True, segments=None, out=None):
    """gangplank_<ship_id>.bbmodel: a medieval folding boarding plank of the given width and length (blocks) in a style,
    drawn straight: one bone "seg_<k>" per segment (origin at its inner end, (k s, 0, 0)), hinged to the next one by
    side plates and knuckles around the joint's fold pivot (odd joints: FOLD_OVER over the walking surface, even ones:
    FOLD_UNDER under it, see core/Gangplank.java), each with its two handrails "rail_<k>_0" (-z) and "rail_<k>_1" (+z),
    whose stanchions fold flat inwards about the line (RAIL_PIVOT_V, +-(width/2 - RAIL_PIVOT_INSET)).
    handrails: posts and rails along both sides of every segment (rope for the wooden styles, rails for the others)."""
    _setup("gangplank_" + ship_id)
    plank, dark, rail, metal, cord, accent, rope_rail, chain = _style(style)
    W, L = float(width), float(length)
    hw = W / 2
    N = segment_count(L, segments)
    S = L / N
    root = Bone("gangplank")
    segs = [Bone("seg_%d" % k, origin=(k * S, 0, 0), parent=root) for k in range(N)]
    pz = hw - RAIL_PIVOT_INSET
    rails = [[Bone("rail_%d_%d" % (k, side), origin=(k * S, RAIL_PIVOT_V, (1 if side else -1) * pz), parent=segs[k])
              for side in (0, 1)] for k in range(N)]

    def seg_at(x):
        return max(0, min(N - 1, int(x // S)))

    def span(i):
        return i * S, (i + 1) * S

    bevel = 0.28
    gap = 0.012          # half the gap between two segments
    # boards along the plank (slightly irregular widths and lengths), top at y = 0, cut at the joints
    n = max(3, int(round(W / 0.42)))
    bw = W / n
    for k in range(n):
        z0 = -hw + k * bw
        bx0 = 0.04 + (0.03 if k % 2 else 0.0)
        bx1 = L - bevel - (0.02 if k % 3 == 1 else 0.0)
        top = 0.0 if k % 2 == 0 else -0.006
        for i in range(N):
            u0, u1 = span(i)
            x0, x1 = max(bx0, u0 + gap), min(bx1, u1 - gap)
            if x1 - x0 < 0.05:
                continue
            _box(segs[i], "board_%d_%d" % (i, k), x0, top - BOARD_TH, z0 + 0.01, x1, top, z0 + bw - 0.01,
                 {"all": R(style, "plank"), "+1": R(style, "end"), "-1": R(style, "end")}, u_dir=v3(1, 0, 0))
        # the bevelled tip: the last bit of each board tilted down to meet the quay
        a = math.radians(14)
        c = v3(bx1 + bevel / 2 * math.cos(a), top - BOARD_TH / 2 - bevel / 2 * math.sin(a), z0 + bw / 2)
        add_cube(segs[N - 1], "tip_%d" % k, c, gg.rz(-a), (bevel + 0.02, BOARD_TH, bw - 0.02),
                 {"all": R(style, "plank"), "+1": R(style, "end"), "-1": R(style, "end")}, u_dir=v3(1, 0, 0))
    # cleats across the walking surface (grip), every ~0.45 block, none on a joint
    nc = max(3, int((L - 0.6) / 0.45))
    for k in range(nc):
        x = 0.35 + k * (L - 0.75) / max(1, nc - 1)
        if style == "worn" and k == nc // 2:
            continue   # one cleat lost
        if any(abs(x - j * S) < 0.1 for j in range(1, N)):
            continue
        _box(segs[seg_at(x)], "cleat_%d" % k, x - 0.05, 0.0, -hw + 0.12, x + 0.05, 0.035, hw - 0.12, R(style, "board"), u_dir=v3(0, 0, 1))
    for i in range(N):
        u0, u1 = span(i)
        sg = segs[i]
        # side stringers under the boards, cross battens at both ends of the segment
        for side in (-1, 1):
            z = side * (hw - 0.07)
            _box(sg, "stringer_%d_%d" % (i, side > 0), u0 + (0.0 if i == 0 else gap), -BOARD_TH - STRINGER_H, z - 0.065,
                 min(u1 - gap, L - 0.05), -BOARD_TH + 0.005, z + 0.065,
                 {"all": R(style, "rail"), "+1": R(style, "end"), "-1": R(style, "end")}, u_dir=v3(1, 0, 0))
        for k, x in enumerate((u0 + (0.5 if i == 0 else 0.2), min(u1 - 0.2, L - 0.55))):
            _box(sg, "batten_%d_%d" % (i, k), x - 0.08, -BOARD_TH - 0.1, -hw + 0.14, x + 0.08, -BOARD_TH + 0.002, hw - 0.14,
                 R(style, "board"), u_dir=v3(0, 0, 1))
        # metal side straps wrapping the stringers and the board ends
        for k, x in enumerate((u0 + 0.3, min(u1 - 0.3, L - 0.35))):
            for side in (-1, 1):
                z = side * (hw + 0.004)
                _box(sg, "strap_%d_%d_%d" % (i, k, side > 0), x - 0.045, -BOARD_TH - STRINGER_H - 0.012, z - 0.012, x + 0.045, 0.012,
                     z + 0.012, R(style, "metal"))
            _box(sg, "strap_bottom_%d_%d" % (i, k), x - 0.045, -BOARD_TH - STRINGER_H - 0.014, -hw, x + 0.045,
                 -BOARD_TH - STRINGER_H + 0.002, hw, R(style, "metal"))
    a = math.radians(14)
    c = v3(L - bevel - 0.02 + (bevel + 0.06) / 2 * math.cos(a), -BOARD_TH - 0.012 - (bevel / 2) * math.sin(a), 0)
    add_cube(segs[N - 1], "tip_shoe", c, gg.rz(-a), (bevel + 0.08, 0.025, W - 0.06), R(style, "metal"))
    # the hinge on the ship: a pin along the hinge line, knuckles on the plank and leaves on the boards
    _knuckle(segs[0], "hinge_pin", 0.0, -0.06, -hw + 0.02, hw - 0.02, 0.035, R(style, "metal"))
    for k, zc in enumerate(np.linspace(-hw + 0.22, hw - 0.22, 3 if W >= 2.5 else 2)):
        _knuckle(segs[0], "knuckle_%d" % k, 0.0, -0.06, zc - 0.13, zc + 0.13, 0.075, R(style, "metal"))
        _box(segs[0], "leaf_%d" % k, 0.04, 0.0, zc - 0.1, 0.42, 0.014, zc + 0.1, R(style, "metal"))
    # the joints between segments: a side plate on each segment reaching the fold pivot, a knuckle round it, a pin
    for j in range(1, N):
        x = j * S
        top = j % 2 == 1
        pv = FOLD_OVER if top else -FOLD_UNDER
        lo, hi = (-0.13, pv) if top else (pv, -0.05)
        for side in (-1, 1):
            # (plate z band, knuckle z band inside it: no coplanar faces closer than zfight.TOL, so nothing is pushed)
            for which, (zi, zo, ki, ko, x0, x1) in enumerate(((0.012, 0.035, 0.02, 0.027, x - PLATE, x),
                                                              (0.042, 0.064, 0.05, 0.056, x, x + PLATE))):
                b = segs[j - 1 + which]
                z0, z1 = sorted((side * (hw + zi), side * (hw + zo)))
                _box(b, "joint_plate_%d_%d_%d" % (j, side > 0, which), x0, lo, z0, x1, hi, z1, R(style, "metal"))
                z0, z1 = sorted((side * (hw + ki), side * (hw + ko)))
                # one cube each (the two crossed cubes of _knuckle would share their end faces and be pushed apart)
                add_cube(b, "joint_knuckle_%d_%d_%d" % (j, side > 0, which), (x, pv, (z0 + z1) / 2), gg.rz(math.pi / 4),
                         (HINGE_R * 1.7, HINGE_R * 1.7, z1 - z0), R(style, "metal"))
            z0, z1 = sorted((side * (hw + 0.004), side * (hw + 0.072)))
            _box(segs[j - 1], "joint_pin_%d_%d" % (j, side > 0), x - 0.017, pv - 0.017, z0, x + 0.017, pv + 0.017, z1, R(style, "accent"))
    # eyes at the outer corners for the support chains / ropes
    for side in (-1, 1):
        z = side * (hw - 0.08)
        _knuckle(segs[N - 1], "eye_%d" % (side > 0), L - 0.25, 0.06, z - 0.03, z + 0.03, 0.06, R(style, "metal"))
        _box(segs[N - 1], "eye_plate_%d" % (side > 0), L - 0.36, 0.0, z - 0.06, L - 0.14, 0.012, z + 0.06, R(style, "metal"))
    # handrails: on every segment, posts along both sides (in a socket on the board edge, folding flat inwards about
    # it) and a rail between them (rope for the wooden styles)
    if handrails and L >= 2.0:
        hgt = 0.82
        for i in range(N):
            u0, u1 = span(i)
            xa, xb = u0 + 0.25, min(u1 - 0.25, L - 0.55)
            npost = 3 if xb - xa > 1.3 else 2
            xs = [xa + k * (xb - xa) / (npost - 1) for k in range(npost)]
            for side in (-1, 1):
                rb = rails[i][side > 0]
                z = side * pz
                tops = []
                for k, x in enumerate(xs):
                    _box(segs[i], "socket_%d_%d_%d" % (i, side > 0, k), x - 0.06, 0.0, z - 0.055, x + 0.06, 0.07, z + 0.055,
                         R(style, "metal"))
                    beam(rb, "post_%d_%d_%d" % (i, side > 0, k), v3(x, RAIL_PIVOT_V - 0.04, z), v3(x, hgt, z), 0.075, R(style, "rail"))
                    if style in ("crystal", "jade", "elven", "copper"):
                        _box(rb, "post_cap_%d_%d_%d" % (i, side > 0, k), x - 0.055, hgt, z - 0.055, x + 0.055, hgt + 0.06, z + 0.055,
                             R(style, "accent"))
                    tops.append(v3(x, hgt - 0.05, z))
                for k in range(npost - 1):
                    a, b = tops[k], tops[k + 1]
                    if rope_rail:
                        sag = 0.07 if style != "worn" else 0.12
                        pts = [a + (b - a) * t - UP * (4 * sag * t * (1 - t)) for t in (0.0, 0.25, 0.5, 0.75, 1.0)]
                        for q in range(4):
                            beam(rb, "rope_%d_%d_%d_%d" % (i, side > 0, k, q), pts[q], pts[q + 1], 0.04, R(style, "cord"), extend=0.01)
                    else:
                        beam(rb, "rail_%d_%d_%d" % (i, side > 0, k), a, b, 0.06, R(style, "rail"), extend=0.03)
                        m = (a + b) / 2 - UP * 0.36
                        beam(rb, "midrail_%d_%d_%d" % (i, side > 0, k), a - UP * 0.36, b - UP * 0.36, 0.04, R(style, "rail"), extend=0.02)
                        if style in ("copper", "steel", "crystal"):
                            beam(rb, "brace_%d_%d_%d" % (i, side > 0, k), a - UP * 0.68, m + UP * 0.02, 0.03, R(style, "metal"))
    # style touches, cut at the joints (clear of the hinge plates)
    for i in range(N):
        u0, u1 = span(i)
        x0, x1 = max(0.1, u0 + PLATE + 0.04), min(L - 0.4, u1 - PLATE - 0.04)
        if x1 - x0 < 0.1:
            continue
        for side in (-1, 1):
            if style == "jade":
                _box(segs[i], "lacquer_band_%d_%d" % (i, side > 0), x0, -BOARD_TH - STRINGER_H * 0.6, side * (hw + 0.01) - 0.008,
                     x1, -BOARD_TH - STRINGER_H * 0.3, side * (hw + 0.01) + 0.008, R(style, "accent"))
            if style == "crystal":
                _box(segs[i], "glow_strip_%d_%d" % (i, side > 0), max(x0, 0.2), -BOARD_TH - 0.06, side * (hw + 0.012) - 0.006, x1,
                     -BOARD_TH - 0.035, side * (hw + 0.012) + 0.006, R(style, "accent"))
    if style == "worn":
        x0 = L * 0.42
        i = seg_at(x0)
        x0 = max(x0, i * S + 0.1)
        x1 = min(x0 + 0.34, (i + 1) * S - 0.1)
        _box(segs[i], "patch", x0, 0.002, -hw * 0.3, x1, 0.03, hw * 0.25, R(style, "board"), u_dir=v3(0, 0, 1))
    return export(root, "gangplank_" + ship_id, out)


# ---------------------------------------------------------------- the lever
def make_lever(style, out=None):
    """gangplank_lever_<style>.bbmodel: a deck lever (base plate, bracket, bone "handle" pivoting at (0, PIVOT_Y, 0))."""
    _setup("gangplank_lever_" + style)
    _style(style)
    root = Bone("lever")
    base = Bone("base", parent=root)
    _box(base, "plate", -0.26, 0.0, -0.2, 0.26, 0.05, 0.2, R(style, "board") if style != "steel" else R(style, "rail"), u_dir=v3(1, 0, 0))
    for side in (-1, 1):
        _box(base, "cheek_%d" % (side > 0), -0.13, 0.05, side * 0.075 - 0.025, 0.13, 0.25, side * 0.075 + 0.025, R(style, "metal"))
        for sx in (-1, 1):
            _box(base, "bolt_%d_%d" % (side > 0, sx > 0), sx * 0.2 - 0.025, 0.05, side * 0.13 - 0.025, sx * 0.2 + 0.025, 0.075,
                 side * 0.13 + 0.025, R(style, "metal"))
    _knuckle(base, "pivot", 0.0, PIVOT_Y, -0.11, 0.11, 0.035, R(style, "metal"))
    # quadrant with the two notches (stowed / deployed)
    for k, a in enumerate((-40, -20, 0, 20, 40)):
        r = math.radians(a)
        c = v3(math.sin(r) * 0.15, PIVOT_Y + math.cos(r) * 0.15 - 0.06, 0.0)
        add_cube(base, "quadrant_%d" % k, c, gg.rz(-r), (0.07, 0.03, 0.05), R(style, "metal"))
    handle = Bone("handle", origin=(0, PIVOT_Y, 0), parent=root)
    beam(handle, "shaft", v3(0, PIVOT_Y - 0.04, 0), v3(0, 0.82, 0), 0.06, R(style, "handle"))
    _box(handle, "ferrule", -0.04, 0.6, -0.04, 0.04, 0.66, 0.04, R(style, "metal"))
    _box(handle, "grip", -0.055, 0.74, -0.055, 0.055, 0.9, 0.055, R(style, "knob"))
    return export(root, "gangplank_lever_" + style, out)


def specs():
    """Every gangplank spec present: {ship id: dict}."""
    import json
    d = os.path.join(ASSETS, "gangplanks")
    out = {}
    if os.path.isdir(d):
        for f in sorted(os.listdir(d)):
            if f.endswith(".json"):
                with open(os.path.join(d, f)) as fh:
                    out[f[:-5]] = json.load(fh)
    return out


def main():
    atlas()
    for s in STYLES:
        make_lever(s)
    for ship, spec in specs().items():
        make_plank(ship, spec["width"], spec["length"], spec["style"], handrails=spec.get("handrails", True),
                   segments=spec.get("segments"))


if __name__ == "__main__":
    main()
