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
  x = length, eyes for the support chains on the last segment's wings (x = length - 0.25, z = +-(width/2 - 0.16)). It
  telescopes and folds into a small flat pack (1.23.2): one bone "seg_<k>" per telescoping segment (segment_count,
  origin (k s, 0, 0); the centre strip, half the width), its side wings "wing_<k>_0" / "wing_<k>_1" (a quarter each,
  hinged lengthwise, a hull-coloured camouflage skin under them: CAMO), the handrail of each wing in "rail_<k>_0" /
  "rail_<k>_1". No animation: the mod folds the wings, slides the segments and telescopes the handrails itself
  (core/Gangplank.java documents the folding and how the model frame maps to the ship).
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

# per style: a 128 x 32 cell of the atlas; inside a cell: (u, v, w, h)
_CELL = {"plank": (0, 0, 64, 16), "board": (0, 16, 64, 16), "rail": (64, 0, 32, 16), "metal": (96, 0, 16, 16),
         "cord": (112, 0, 16, 16), "end": (64, 16, 16, 16), "accent": (80, 16, 16, 16), "handle": (96, 16, 16, 16),
         "knob": (112, 16, 16, 16)}
REGIONS = {}
for _i, _s in enumerate(STYLES):
    _ox, _oy = (_i % 2) * 128, (_i // 2) * 32
    for _k, (_u, _v, _w, _h) in _CELL.items():
        REGIONS["%s_%s" % (_s, _k)] = (_ox + _u, _oy + _v, _w, _h)

# Camouflage of the stowed pack (1.23.2): per vessel, the colours of its hull where the pack lies (skin, its darker
# seams) and of the band under the hinge (trim), sampled from the ship models by `ships_g2.py camo`; one 64 x 16 cell
# per vessel in the lower half of the atlas: the skin (48 x 16, planks running along u) and the trim (16 x 16).
CAMO_SHIPS = ("galley", "galleon", "warship", "medieval_galley", "steam_paddleboat", "elven_sailboat", "old_corsair",
              "blue_frigate", "steampunk_airship", "crystal_airship", "sky_leviathan", "dragon_junk")
CAMO = {
    # ship: (skin, seams, trim)            -- from `python3 tools/gangplank/ships_g2.py camo`
    'galley': ('964526', '5a1814', 'bb8648'),
    'galleon': ('ba8542', '513317', 'd69a4e'),
    'warship': ('282320', '1b1714', '2e2822'),
    'medieval_galley': ('c65b3f', '941d18', 'e6c060'),
    'steam_paddleboat': ('323336', '272924', 'e0b54e'),
    'elven_sailboat': ('99897a', '266a3b', 'cea34d'),
    'old_corsair': ('6b4326', '382413', '734c2c'),
    'blue_frigate': ('d2a036', '694d10', 'efcb5b'),
    'crystal_airship': ('945e2e', '674222', '684222'),
    'sky_leviathan': ('7e5639', '5f422c', '5c3b21'),
    'dragon_junk': ('c7b99d', '746650', '5c3a24'),
    'steampunk_airship': ('704a2a', '48301a', 'a77d28'),
}
for _i, _s in enumerate(CAMO_SHIPS):
    _ox, _oy = (_i % 4) * 64, 128 + (_i // 4) * 16
    REGIONS["camo_%s_skin" % _s] = (_ox, _oy, 48, 16)
    REGIONS["camo_%s_trim" % _s] = (_ox + 48, _oy, 16, 16)


def camo_regions(ship_id):
    """Atlas regions of a vessel's camouflage ({"skin", "trim"}); a vessel without a cell gets worn wood and iron."""
    if ship_id in CAMO_SHIPS:
        return {"skin": "camo_%s_skin" % ship_id, "trim": "camo_%s_trim" % ship_id}
    return {"skin": "worn_board", "trim": "worn_metal"}


def _camo_cells(img, rng):
    for ship in CAMO_SHIPS:
        skin, seams, trim = (_rgb(c) for c in CAMO.get(ship, ("7a5a3a", "3e2c1c", "c9a24a")))
        reg = REGIONS["camo_%s_skin" % ship]
        if ship == "steam_paddleboat":
            _rivets(img, reg, skin, rng, step=12)
        else:
            fine_wood(img, reg, skin, seams, 4, rng, joints=True, knots=0.05, grain=0.06, shade=0.05)
        polished_metal(img, REGIONS["camo_%s_trim" % ship], [(0.0, _scale(trim, 0.6)), (0.5, trim), (0.85, _scale(trim, 1.18)),
                                                            (1.0, _scale(trim, 1.3))], rng)


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
    _camo_cells(img, random.Random(1232))
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
# Compact folding geometry (1.23.2), as core/Gangplank.java (SEGMENT, MAX_SEGMENTS, BOARD, STRIP_DEPTH, WING_DEPTH,
# WING_PIVOT, WING_GAP, RAIL_INSET, stripHalf, wingPivot)
SEGMENT = 0.8
MAX_SEGMENTS = 20
BOARD = 0.05         # board thickness (walking surface at y = 0)
STRIP_DEPTH = 0.11   # the centre strip under its walking surface (boards, stringers, strap)
WING_DEPTH = 0.074   # a side wing under its walking surface (boards, camouflage skin, trim strips)
WING_PIVOT = 0.07    # the wings' hinge axis, this high over the walking surface...
WING_GAP = 0.02      # ...and this far outboard of the strip's edge (the folded wings leave 2 x WING_GAP between them)
WING_KNUCKLE_R = 0.032
RAIL_INSET = 0.04    # the handrails' posts, this far inside the plank's side edges
RAIL_H = 0.82
SEAM = 0.012         # half the gap between two telescoping segments


def segment_count(length, segments=None):
    """core/Gangplank.segments: the override, else ceil(length / SEGMENT), at least 2."""
    n = int(segments) if segments else int(math.ceil(length / SEGMENT - 1e-9))
    return max(2, min(MAX_SEGMENTS, n))


def strip_width(width):
    """core/Gangplank.stripHalf * 2: the centre strip is half the plank, each side wing a quarter."""
    return width / 2.0


def make_plank(ship_id, width, length, style, handrails=True, segments=None, out=None):
    """gangplank_<ship_id>.bbmodel: a medieval boarding plank of the given width and length (blocks) in a style, drawn
    straight (deployed), that telescopes and folds into a small flat pack (1.23.2, see core/Gangplank.java):
    - one bone "seg_<k>" per telescoping segment (origin at its inner end, (k s, 0, 0)): the centre strip (half the
      width: boards, cleats, stringers, battens, strap; the ship hinge on seg_0, the bevelled tip on the last one);
    - its two side wings "wing_<k>_0" (-z) and "wing_<k>_1" (+z), children of seg_<k>, origin on their hinge axis
      (k s, WING_PIVOT, +-(width / 4 + WING_GAP)): boards, the hull-coloured skin under them (camouflage of the ship,
      CAMO) with trim strips along its edges, a knuckle on the axis; stowed they fold over the strip's walking surface;
    - the handrail of each wing "rail_<k>_<side>" (one post per segment, a rope or rail back to the previous post),
      child of its wing, origin at the post's foot (k s, 0, +-(width / 2 - RAIL_INSET)); its posts telescope down.
    Parts mounted on a surface sink 0.01 into it and stacked layers stay 0.012 apart, so that no two faces are coplanar
    (zfight would push them apart and thicken the pack).
    handrails: posts and rails along both sides (rope for the wooden styles, rails for the others)."""
    _setup("gangplank_" + ship_id)
    plank, dark, rail, metal, cord, accent, rope_rail, chain = _style(style)
    camo = camo_regions(ship_id)
    W, L = float(width), float(length)
    hw = W / 2
    hc = strip_width(W) / 2
    pz = hc + WING_GAP
    N = segment_count(L, segments)
    S = L / N
    EMB = 0.01           # how far a mounted part sinks into what carries it
    root = Bone("gangplank")
    segs = [Bone("seg_%d" % k, origin=(k * S, 0, 0), parent=root) for k in range(N)]
    wings = [[Bone("wing_%d_%d" % (k, side), origin=(k * S, WING_PIVOT, (1 if side else -1) * pz), parent=segs[k])
              for side in (0, 1)] for k in range(N)]
    rz = hw - RAIL_INSET
    rails = [[Bone("rail_%d_%d" % (k, side), origin=(k * S, 0, (1 if side else -1) * rz), parent=wings[k][side])
              for side in (0, 1)] for k in range(N)]
    bevel = 0.28
    a14 = math.radians(14)
    end_faces = {"all": R(style, "plank"), "+1": R(style, "end"), "-1": R(style, "end")}

    def span(i):
        u0, u1 = i * S, (i + 1) * S
        x0 = 0.04 if i == 0 else u0 + SEAM
        x1 = L - bevel if i == N - 1 else u1 - SEAM
        return u0, u1, x0, x1

    def boards(bone, i, z_lo, z_hi, tag, top_parity):
        """Boards along the plank between z_lo and z_hi (top at y = 0), the bevelled tip on the last segment."""
        u0, u1, x0, x1 = span(i)
        nb = max(1, int(round((z_hi - z_lo) / 0.42)))
        bw = (z_hi - z_lo) / nb
        for k in range(nb):
            z0 = z_lo + k * bw
            top = 0.0 if (k + top_parity) % 2 == 0 else -0.004
            _box(bone, "board_%s_%d_%d" % (tag, i, k), x0, top - BOARD, z0 + 0.008, x1, top, z0 + bw - 0.008, end_faces,
                 u_dir=v3(1, 0, 0))
            if i == N - 1:
                c = v3(x1 + bevel / 2 * math.cos(a14), top - BOARD / 2 - bevel / 2 * math.sin(a14), z0 + bw / 2)
                add_cube(bone, "tip_%s_%d" % (tag, k), c, gg.rz(-a14), (bevel + 0.02, BOARD, bw - 0.016), end_faces, u_dir=v3(1, 0, 0))

    def cleats(bone, i, z_lo, z_hi, tag):
        u0, u1, x0, x1 = span(i)
        nc = max(1, int(round((x1 - x0) / 0.42)))
        for k in range(nc):
            x = x0 + (k + 0.5) * (x1 - x0) / nc
            if style == "worn" and (i * 7 + k) % 9 == 4:
                continue   # a cleat lost here and there
            _box(bone, "cleat_%s_%d_%d" % (tag, i, k), x - 0.045, -0.02, z_lo, x + 0.045, 0.032, z_hi, R(style, "board"), u_dir=v3(0, 0, 1))

    def knuckle(bone, name, x0, x1, y, z, r, region):
        """A hinge barrel along the plank (one square section turned 45 degrees: no shared end faces)."""
        add_cube(bone, name, ((x0 + x1) / 2, y, z), gg.rx(math.pi / 4), (x1 - x0, r * 1.6, r * 1.6), region)

    def barrel_z(bone, name, x, y, z0, z1, r, region):
        """A barrel across the plank (along z), one square section turned 45 degrees."""
        add_cube(bone, name, (x, y, (z0 + z1) / 2), gg.rz(math.pi / 4), (r * 1.6, r * 1.6, z1 - z0), region)

    for i in range(N):
        u0, u1, x0, x1 = span(i)
        sg = segs[i]
        # ---- the centre strip
        boards(sg, i, -hc, hc, "s", 0)
        cleats(sg, i, -hc + 0.07, hc - 0.07, "s")
        for side in (-1, 1):
            z = side * (hc - 0.07)
            _box(sg, "stringer_%d_%d" % (i, side > 0), x0 + 0.012, -STRIP_DEPTH + 0.012, z - 0.05, x1 - 0.012, -BOARD + EMB, z + 0.05,
                 {"all": R(style, "rail"), "+1": R(style, "end"), "-1": R(style, "end")}, u_dir=v3(1, 0, 0))
        bx = sorted({min(x0 + 0.12, (x0 + x1) / 2), max(x1 - 0.12, (x0 + x1) / 2)})
        for k, x in enumerate(bx):
            _box(sg, "batten_%d_%d" % (i, k), x - 0.05, -STRIP_DEPTH + 0.024, -hc + 0.13, x + 0.05, -BOARD + EMB, hc - 0.13,
                 R(style, "board"), u_dir=v3(0, 0, 1))
        xm = (bx[0] + bx[-1]) / 2 if len(bx) > 1 else bx[0] + 0.1
        _box(sg, "strap_bottom_%d" % i, xm - 0.035, -STRIP_DEPTH, -hc + 0.03, xm + 0.035, -STRIP_DEPTH + 0.024, hc - 0.03, R(style, "metal"))
        # the wings' hinges: a barrel on the strip, on the axis (the wing's own barrel is further along), its web and leaf
        for side in (-1, 1):
            z = side * pz
            ka, kb = u0 + 0.06, u0 + min(0.26, S * 0.4)
            knuckle(sg, "wing_knuckle_s_%d_%d" % (i, side > 0), ka, kb, WING_PIVOT, z, WING_KNUCKLE_R, R(style, "metal"))
            z0, z1 = sorted((side * (pz - 0.012), side * (pz + 0.006)))
            _box(sg, "wing_web_s_%d_%d" % (i, side > 0), ka + 0.02, -0.03, z0, kb - 0.02, WING_PIVOT, z1, R(style, "metal"))
            z0, z1 = sorted((side * (hc - 0.05), side * (pz - 0.004)))
            _box(sg, "wing_leaf_s_%d_%d" % (i, side > 0), ka + 0.03, -EMB, z0, kb - 0.03, 0.012, z1, R(style, "metal"))
        # ---- the two side wings (in plank coordinates; the bone origin is the hinge axis)
        for side in (-1, 1):
            wb = wings[i][side > 0]
            zi, zo = side * (hc + 0.006), side * hw
            z_lo, z_hi = sorted((zi, zo))
            boards(wb, i, z_lo, z_hi, "w%d" % (side > 0), 1)
            ci, co = side * (hc + 0.08), side * (hw - 0.13)
            if abs(co) - abs(ci) > 0.1:
                cleats(wb, i, min(ci, co), max(ci, co), "w%d" % (side > 0))
            # camouflage skin under the boards (the outer face of the stowed pack), trim strips along its edges
            t = 0.045
            za, zb = sorted((zi + side * 0.02, zo - side * 0.02))
            _box(wb, "skin_%d_%d" % (i, side > 0), x0 + 0.02, -WING_DEPTH + 0.012, za, x1 - 0.02, -BOARD + 0.015, zb,
                 camo["skin"], u_dir=v3(0, 0, 1))
            z0, z1 = sorted((zo - side * t, zo + side * 0.01))
            _box(wb, "trim_out_%d_%d" % (i, side > 0), x0 + 0.012, -WING_DEPTH, z0, x1 - 0.012, -0.012, z1, camo["trim"], u_dir=v3(1, 0, 0))
            z0, z1 = sorted((zi, zi + side * t))
            _box(wb, "trim_in_%d_%d" % (i, side > 0), x0 + 0.012, -WING_DEPTH, z0, x1 - 0.012, -BOARD + 0.003, z1, camo["trim"], u_dir=v3(1, 0, 0))
            z0, z1 = sorted((zi + side * (t + 0.012), zo - side * (t + 0.012)))
            for name, (a, b) in (("lo", (x0 + 0.012, x0 + 0.012 + t)), ("hi", (x1 - 0.012 - t, x1 - 0.012))):
                _box(wb, "trim_%s_%d_%d" % (name, i, side > 0), a, -WING_DEPTH, z0, b, -BOARD + 0.003, z1, camo["trim"], u_dir=v3(0, 0, 1))
            # the wing's barrel on the axis, its web and leaf on the wing's boards
            ka, kb = u1 - min(0.26, S * 0.4), u1 - 0.06
            knuckle(wb, "wing_knuckle_w_%d_%d" % (i, side > 0), ka, kb, WING_PIVOT, side * pz, WING_KNUCKLE_R, R(style, "metal"))
            z0, z1 = sorted((side * (pz - 0.006), side * (pz + 0.012)))
            _box(wb, "wing_web_w_%d_%d" % (i, side > 0), ka + 0.02, -0.03, z0, kb - 0.02, WING_PIVOT, z1, R(style, "metal"))
            z0, z1 = sorted((side * (pz + 0.004), side * (pz + 0.09)))
            _box(wb, "wing_leaf_w_%d_%d" % (i, side > 0), ka + 0.03, -EMB, z0, kb - 0.03, 0.012, z1, R(style, "metal"))
    # the bevelled tip's shoe (strip and wings) and the eyes for the support chains / ropes, on the wings
    for part, (z0, z1) in (("s", (-hc + 0.02, hc - 0.02)), ("w0", (-hw + 0.03, -hc - 0.02)), ("w1", (hc + 0.02, hw - 0.03))):
        bone = segs[N - 1] if part == "s" else wings[N - 1][part == "w1"]
        c = v3(L - bevel - 0.02 + (bevel + 0.06) / 2 * math.cos(a14), -BOARD - 0.012 - (bevel / 2) * math.sin(a14), (z0 + z1) / 2)
        add_cube(bone, "tip_shoe_%s" % part, c, gg.rz(-a14), (bevel + 0.08, 0.02, z1 - z0), R(style, "metal"))
    for side in (-1, 1):
        z = side * (hw - 0.16)
        wb = wings[N - 1][side > 0]
        barrel_z(wb, "eye_%d" % (side > 0), L - 0.25, 0.05, z - 0.03, z + 0.03, 0.05, R(style, "metal"))
        _box(wb, "eye_plate_%d" % (side > 0), L - 0.34, -0.026, z - 0.055, L - 0.16, 0.012, z + 0.055, R(style, "metal"))
    # the hinge on the ship: a pin along the hinge line under the strip, knuckles and leaves on its boards
    barrel_z(segs[0], "hinge_pin", 0.0, -0.05, -hc + 0.02, hc - 0.02, 0.03, R(style, "metal"))
    for k, zc in enumerate(np.linspace(-hc + 0.18, hc - 0.18, 2)):
        barrel_z(segs[0], "knuckle_%d" % k, 0.0, -0.05, zc - 0.1, zc + 0.1, 0.05, R(style, "metal"))
        _box(segs[0], "leaf_%d" % k, 0.055, -EMB, zc - 0.08, 0.3, 0.012, zc + 0.08, R(style, "metal"))
    # handrails: one post per segment on each wing's outer edge (a socket at its foot), a rope or rail back to the
    # previous segment's post; they telescope down (core/Gangplank: the mod scales them) when stowed or moving
    if handrails and L >= 2.0:
        xs = [min(i * S + 0.4 * S, L - 0.45) for i in range(N)]
        for i in range(N):
            for side in (-1, 1):
                rb = rails[i][side > 0]
                z = side * rz
                x = xs[i]
                _box(rb, "socket_%d_%d" % (i, side > 0), x - 0.055, -0.035, z - 0.05, x + 0.055, 0.06, z + 0.05, R(style, "metal"))
                beam(rb, "post_%d_%d" % (i, side > 0), v3(x, 0.02, z), v3(x, RAIL_H, z), 0.07, R(style, "rail"))
                if style in ("crystal", "jade", "elven", "copper"):
                    _box(rb, "post_cap_%d_%d" % (i, side > 0), x - 0.05, RAIL_H - 0.02, z - 0.05, x + 0.05, RAIL_H + 0.05, z + 0.05,
                         R(style, "accent"))
                if i == 0:
                    continue
                a, b = v3(xs[i - 1], RAIL_H - 0.05, z), v3(x, RAIL_H - 0.05, z)
                if rope_rail:
                    sag = 0.05 if style != "worn" else 0.09
                    pts = [a + (b - a) * t - UP * (4 * sag * t * (1 - t)) for t in (0.0, 0.33, 0.67, 1.0)]
                    for q in range(3):
                        beam(rb, "rope_%d_%d_%d" % (i, side > 0, q), pts[q], pts[q + 1], 0.04, R(style, "cord"), extend=0.01)
                else:
                    beam(rb, "rail_%d_%d" % (i, side > 0), a, b, 0.055, R(style, "rail"), extend=0.025)
                    beam(rb, "midrail_%d_%d" % (i, side > 0), a - UP * 0.36, b - UP * 0.36, 0.04, R(style, "rail"), extend=0.015)
                    if style in ("copper", "steel", "crystal"):
                        beam(rb, "brace_%d_%d" % (i, side > 0), a - UP * 0.68, (a + b) / 2 - UP * 0.34, 0.03, R(style, "metal"))
    # style touches on the strip's sides
    for i in range(N):
        u0, u1, x0, x1 = span(i)
        for side in (-1, 1):
            if style == "jade":
                _box(segs[i], "lacquer_band_%d_%d" % (i, side > 0), x0 + 0.05, -STRIP_DEPTH + 0.03, side * (hc - 0.02) - 0.006,
                     x1 - 0.05, -BOARD - 0.012, side * (hc - 0.02) + 0.006, R(style, "accent"))
            if style == "crystal":
                _box(segs[i], "glow_strip_%d_%d" % (i, side > 0), x0 + 0.05, -BOARD - 0.035, side * (hc - 0.015) - 0.005, x1 - 0.05,
                     -BOARD - 0.015, side * (hc - 0.015) + 0.005, R(style, "accent"))
    if style == "worn":
        i = min(N - 1, int(L * 0.42 // S))
        u0, u1, x0, x1 = span(i)
        _box(segs[i], "patch", x0 + 0.05, -EMB, -hc * 0.6, min(x1 - 0.05, x0 + 0.36), 0.028, hc * 0.5, R(style, "board"), u_dir=v3(0, 0, 1))
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
