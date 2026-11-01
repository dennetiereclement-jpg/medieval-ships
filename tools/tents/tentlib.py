"""Shared helpers of the six tents (one block each, drawn like the ships from a .bbmodel).

A tent generator (tools/tents/generate_<tent>.py) does, in this order:

    import tentlib as tl
    tl.setup()                                   # the shared atlas (tent_texture.py) becomes the regions
    root = tl.Bone("tent_x")
    ... tl.post / tl.rope / tl.canvas_panel / tl.cone_roof / tl.platform / tl.railing / tl.bedroll ...
    tl.collide(box)                              # (x0, y0, z0, x1, y1, z1) tent-local: posts, platforms, solid furniture
    decor = tl.Decor()                           # furniture of the decoration mods, drawn in place (vanilla alt when missing)
    decor.block("furnish:spruce_crate", x, y, z, facing="front", alt="minecraft:barrel", fallback="crate")
    decor.fallbacks(root)                        # stand-in boxes (bones fallback_<i>) shown when the mod is missing
    tl.export(root, "tent_x", decor, icon=my_icon_fn)

export() writes blockbench/<tent>.bbmodel, the assets copy, the shared atlas textures/entity/tents.png, the item icon
textures/item/<tent>.png, interiors/<tent>_decor.json and tents/<tent>.json (extent box + collision boxes), which the
Java TentType reads: nothing to copy by hand. Coordinates: tent-local blocks, y up, +z = the front of the tent (the
side that faces the player who placed it), the anchor block's centre at (0, 0, 0) at ground level.
"""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(HERE, "..")
ROOT = os.path.abspath(os.path.join(TOOLS, ".."))
sys.path.insert(0, TOOLS)
sys.path.insert(0, HERE)
import generate_galley as gg  # noqa: E402
import generate_galleon as gn  # noqa: E402
import tent_texture as tt  # noqa: E402

v3, norm, Bone, add_cube, beam = gg.v3, gg.norm, gg.Bone, gg.add_cube, gg.beam
EYE = np.eye(3)
UP = v3(0, 1, 0)
ASSETS = os.path.join(ROOT, "src/main/resources/assets/medievalships")
CATALOG = "/tmp/claude-0/mods_catalog/catalog.json"

# InteriorDecor yaw of a mod block whose front (its north face) must face a side of the tent (+z = front)
FACING = {"back": 0.0, "neg_x": 90.0, "front": 180.0, "pos_x": 270.0}

# model bounds [minX, maxX, minY, maxY, minZ, maxZ] (block space, default state) of the mod blocks the tents use,
# from the catalog of the user's mods; the catalog file completes this table when it is present
BOUNDS = {
    "furnish:spruce_crate": (0.0, 1.0, 0.0, 1.0, 0.0, 1.0),
    "furnish:oak_crate": (0.0, 1.0, 0.0, 1.0, 0.0, 1.0),
    "furnish:dark_oak_crate": (0.0, 1.0, 0.0, 1.0, 0.0, 1.0),
    "farmersdelight:carrot_crate": (0.0, 1.0, 0.0, 1.0, 0.0, 1.0),
    "farmersdelight:potato_crate": (0.0, 1.0, 0.0, 1.0, 0.0, 1.0),
    "farmersdelight:rice_bag": (0.0, 1.0, 0.0, 1.0, 0.0, 1.0),
    "landsoficaria:cypress_barrel": (0.047, 0.953, 0.0, 0.906, 0.0, 1.0),
    "landsoficaria:loaded_cypress_barrel": (0.047, 0.953, 0.0, 0.906, 0.0, 1.0),
    "farmhouse_decorations:kerosene_lantern": (0.37, 0.63, 0.0, 0.484, 0.375, 0.625),
    "farmhouse_decorations:chained_kerosene_lantern": (0.37, 0.63, 0.328, 1.0, 0.375, 0.625),
    "farmhouse_decorations:single_bed": (-0.109, 1.109, 0.0, 1.141, 0.016, 1.984),
    "minecraft:barrel": (0.0, 1.0, 0.0, 1.0, 0.0, 1.0),
    "minecraft:lantern": (0.3125, 0.6875, 0.0, 0.5625, 0.3125, 0.6875),
    "minecraft:chest": (0.0625, 0.9375, 0.0, 0.875, 0.0625, 0.9375),
}
_uuid_counter = [0]
_NAME = ["tent"]
COLLIDERS = []


def new_uuid():
    import uuid
    _uuid_counter[0] += 1
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "medievalships/%s/%d" % (_NAME[0], _uuid_counter[0])))


def setup(name="tent"):
    """Points the shared generators at the tents' atlas; call first."""
    _NAME[0] = name
    _uuid_counter[0] = 0
    COLLIDERS.clear()
    gg.new_uuid = new_uuid
    gn.new_uuid = new_uuid
    gn.REGIONS = {k: (0,) + r for k, r in tt.REGIONS.items()}
    gn.SIZE = tt.SIZE
    gg.REGIONS = dict(tt.REGIONS)
    gg.SIZE = tt.SIZE
    if os.path.exists(CATALOG):
        try:
            with open(CATALOG) as f:
                for b in json.load(f).get("blocks", []):
                    if b.get("bounds"):
                        BOUNDS.setdefault(b["id"], tuple(b["bounds"]))
        except Exception as e:  # the catalog is a convenience, never a requirement
            print("catalog not read:", e)


# ---------------------------------------------------------------- collision boxes
def collide(box):
    """Declares a tent-local collision box (x0, y0, z0, x1, y1, z1); entities bump into it (EntityCollisionMixin)."""
    x0, y0, z0, x1, y1, z1 = box
    COLLIDERS.append((min(x0, x1), min(y0, y1), min(z0, z1), max(x0, x1), max(y0, y1), max(z0, z1)))


def collide_segment(p0, p1, d, segs=3):
    """Collision boxes of a (leaning) pole from p0 to p1 of thickness d: segs small boxes along it."""
    p0, p1 = v3(*p0), v3(*p1)
    for k in range(segs):
        a, b = p0 + (p1 - p0) * k / segs, p0 + (p1 - p0) * (k + 1) / segs
        lo, hi = np.minimum(a, b) - d / 2, np.maximum(a, b) + d / 2
        collide((lo[0], lo[1], lo[2], hi[0], hi[1], hi[2]))


# ---------------------------------------------------------------- structure
def post(bone, name, foot, top, d=0.18, region="wood", solid=True, cap=True, extend=0.0):
    """A wooden post from foot to top (lean it by giving a top offset); square section d; collides when solid."""
    foot, top = v3(*foot), v3(*top)
    c = beam(bone, name, foot, top, d, {"all": region, "+1": "end_grain", "-1": "end_grain"} if cap else region, extend=extend)
    if solid:
        collide_segment(foot, top, d, segs=max(1, int(math.ceil(np.linalg.norm(top - foot) / 1.2))))
    return c


def pole(bone, name, p0, p1, d=0.12, region="wood", extend=0.0):
    """A thinner pole / beam with no collision (ridge poles, braces, rafters)."""
    return beam(bone, name, p0, p1, d, region, extend=extend)


def rope(bone, name, p0, p1, d=0.05, sag=0.0, segs=1, region="rope"):
    """A rope between two points, sagging in the middle (quadratic, sag in blocks) in segs pieces."""
    p0, p1 = v3(*p0), v3(*p1)
    pts = []
    for k in range(segs + 1):
        t = k / segs
        pts.append(p0 + (p1 - p0) * t - UP * (4 * sag * t * (1 - t)))
    for k in range(segs):
        beam(bone, "%s_%d" % (name, k), pts[k], pts[k + 1], d, region, extend=d * 0.4)


def peg(bone, name, p, towards, length=0.45, d=0.1, region="peg"):
    """A tent peg driven into the ground at p, leaning away from the point it holds (towards)."""
    p, towards = v3(*p), v3(*towards)
    away = towards - p
    away[1] = 0
    away = -norm(away) if np.linalg.norm(away) > 1e-6 else v3(0, 0, 1)
    top = p + UP * length * 0.75 + away * length * 0.35
    foot = p - UP * length * 0.25 - away * length * 0.1
    return beam(bone, name, foot, top, d, {"all": region, "+1": "end_grain", "-1": "end_grain"})


def guy(bone, name, top, ground, sag=0.04, d=0.05):
    """A guy rope from a pole top to a peg in the ground (the peg is added)."""
    rope(bone, name, top, ground, d=d, sag=sag, segs=2)
    peg(bone, name + "_peg", ground, top)


# ---------------------------------------------------------------- cloth
def loft(bone, name, P, nx, ny, region, th=0.03, overlap=0.004, both=True, u_hint=None, v_hint=None):
    """Cloth surface P(s, t) -> point (s across in [0, 1], t down in [0, 1]) made of nx x ny tilted strips, the
    region stretched over the whole surface (each strip maps its own part), both faces textured."""
    for i in range(nx):
        for j in range(ny):
            s0, s1, t0, t1 = i / nx, (i + 1) / nx, j / ny, (j + 1) / ny
            a1, b1, a0, b0 = P(s0, t0), P(s1, t0), P(s0, t1), P(s1, t1)   # a = left, b = right, 1 = top, 0 = bottom
            c = (a0 + a1 + b0 + b1) / 4
            u = ((b0 + b1) - (a0 + a1)) / 2
            L = np.linalg.norm(u)
            if L < 1e-5:
                u = v3(1, 0, 0)
                L = 1e-3
            u = u / L
            vp = ((a0 - a1) + (b0 - b1)) / 2
            H = np.linalg.norm(vp)
            if H < 1e-5:
                continue
            v = norm(vp - np.dot(vp, u) * u)
            n = np.cross(u, v)
            axes = np.column_stack([u, v, n])
            regions = {"all": None, "+3": region, "-3": region} if both else {"all": None, "+3": region}
            cube = add_cube(bone, "%s_%d_%d" % (name, i, j), c, axes, (L + overlap, H + overlap, th), regions, stretch=True,
                            u_dir=u if u_hint is None else u_hint, v_dir=v if v_hint is None else v_hint)
            gn.set_sub(cube, (s0, t0, s1, t1))
    return None


def canvas_panel(bone, name, top0, top1, bot0, bot1, sag=0.15, nx=3, ny=4, region="canvas", th=0.03, ripple=0.05,
                 fringe=0.0, fringe_region="fringe", sag_dir=None):
    """A sagging cloth panel: top0-top1 is its upper edge (on a ridge or a beam), bot0-bot1 its lower edge. The cloth
    bellies by `sag` between the two edges (towards sag_dir, default downwards), the lower edge ripples a little, and
    a torn fringe of height `fringe` hangs on past the lower edge, continuing the slope."""
    top0, top1, bot0, bot1 = (v3(*p) for p in (top0, top1, bot0, bot1))
    nrm = norm(np.cross(top1 - top0, bot0 - top0))
    sd = v3(0, -1, 0) if sag_dir is None else norm(v3(*sag_dir))
    belly = nrm * np.dot(sd, nrm)   # the sag, along the panel's normal, towards sag_dir
    if np.linalg.norm(belly) < 0.2:
        belly = -nrm if nrm[1] > 0 else nrm

    def P(s, t):
        p = (top0 + (top1 - top0) * s) * (1 - t) + (bot0 + (bot1 - bot0) * s) * t
        p = p + belly * (sag * math.sin(math.pi * t) * (0.75 + 0.25 * math.sin(math.pi * s)))
        p = p + belly * (ripple * t * t * math.sin(s * math.pi * 3.0 + 0.4))
        return p

    loft(bone, name, P, nx, ny, region, th=th)
    if fringe > 0:
        down = [norm(P(s, 1.0) - P(s, 0.92)) for s in (0.0, 1.0)]

        def F(s, t):
            d = down[0] * (1 - s) + down[1] * s
            return P(s, 1.0) + d * (fringe * t) + belly * (0.02 * math.sin(s * 11.0))
        loft(bone, name + "_fringe", F, nx, 1, fringe_region, th=th * 0.8)
    return P


def cone_roof(bone, name, apex, base_center, radius, n=10, region="canvas", sag=0.12, ny=4, fringe=0.0,
              fringe_region="fringe", stripes=None, phase=0.0, drop=0.0):
    """A conical canvas roof (pavilions): n wedges from the apex to a circle of `radius` round base_center, the
    cloth sagging between the rafters; `stripes` = list of regions used in turn for the wedges; drop lowers the
    lower edge between the rafters (the scalloped look)."""
    apex, base_center = v3(*apex), v3(*base_center)
    for k in range(n):
        a0, a1 = phase + 2 * math.pi * k / n, phase + 2 * math.pi * (k + 1) / n
        e0 = base_center + v3(math.cos(a0), 0, math.sin(a0)) * radius
        e1 = base_center + v3(math.cos(a1), 0, math.sin(a1)) * radius
        mid = norm((e0 + e1) / 2 - base_center)
        reg = stripes[k % len(stripes)] if stripes else region

        def P(s, t, e0=e0, e1=e1, mid=mid):
            edge = e0 + (e1 - e0) * s
            p = apex * (1 - t) + edge * t
            bulge = math.sin(math.pi * s) * t
            p = p - mid * (sag * bulge) - UP * (drop * bulge + sag * 0.5 * math.sin(math.pi * t) * (1 - abs(2 * s - 1)) * 0.5)
            return p
        loft(bone, "%s_%d" % (name, k), P, 2, ny, reg, th=0.03)
        if fringe > 0:
            def F(s, t, P=P):
                return P(s, 1.0) + norm(P(s, 1.0) - P(s, 0.9)) * fringe * t
            loft(bone, "%s_%d_fringe" % (name, k), F, 2, 1, fringe_region if not stripes else fringe_region, th=0.024)


def pennant(bone, name, top, length=0.7, width=0.3, region="canvas_red", direction=(0, 0, 1)):
    """A small hanging / fluttering cloth tail (no collision)."""
    top, d = v3(*top), norm(v3(*direction))
    side = norm(np.cross(UP, d)) if abs(d[1]) < 0.9 else v3(1, 0, 0)

    def P(s, t):
        return top + side * ((s - 0.5) * width * (1 - 0.5 * t)) + d * (0.25 * length * t) - UP * (length * t) + side * (0.04 * math.sin(t * 6))
    loft(bone, name, P, 1, 3, region, th=0.02)


# ---------------------------------------------------------------- platforms, railings, furniture
def platform(bone, name, x0, x1, z0, z1, y, th=0.1, plank_w=0.5, along="z", region="plank", solid=True, joists=True):
    """A plank floor from (x0, z0) to (x1, z1) with its top at y; collides when solid."""
    if along == "z":
        n = max(1, int(round((x1 - x0) / plank_w)))
        w = (x1 - x0) / n
        for k in range(n):
            xa = x0 + k * w
            dz = (k % 3) * 0.08
            add_cube(bone, "%s_%d" % (name, k), (xa + w / 2, y - th / 2, (z0 + z1) / 2 + dz / 2), EYE, (w * 0.97, th, (z1 - z0) - dz), region,
                     u_dir=v3(0, 0, 1))
    else:
        n = max(1, int(round((z1 - z0) / plank_w)))
        w = (z1 - z0) / n
        for k in range(n):
            za = z0 + k * w
            dx = (k % 3) * 0.08
            add_cube(bone, "%s_%d" % (name, k), ((x0 + x1) / 2 + dx / 2, y - th / 2, za + w / 2), EYE, ((x1 - x0) - dx, th, w * 0.97), region,
                     u_dir=v3(1, 0, 0))
    if joists:
        for k, zz in enumerate((z0 + 0.15, z1 - 0.15)):
            add_cube(bone, "%s_joist_%d" % (name, k), ((x0 + x1) / 2, y - th - 0.06, zz), EYE, (x1 - x0 - 0.1, 0.12, 0.14), "wood_dark")
    if solid:
        collide((x0, y - th - 0.15, z0, x1, y, z1))


def railing(bone, name, p0, p1, h=1.0, post_every=1.4, d=0.1, region="wood", rails=(0.55, 1.0), solid=True):
    """A rustic railing between two points: posts every post_every blocks and horizontal rails; collides as a wall."""
    p0, p1 = v3(*p0), v3(*p1)
    L = np.linalg.norm(p1 - p0)
    n = max(1, int(math.ceil(L / post_every)))
    for k in range(n + 1):
        p = p0 + (p1 - p0) * k / n
        beam(bone, "%s_post_%d" % (name, k), p - UP * 0.05, p + UP * h, d, region)
    for i, r in enumerate(rails):
        beam(bone, "%s_rail_%d" % (name, i), p0 + UP * r * h, p1 + UP * r * h, d * 0.8, "wood_dark", extend=d * 0.4)
    if solid:
        lo, hi = np.minimum(p0, p1), np.maximum(p0, p1)
        collide((lo[0] - d, lo[1], lo[2] - d, hi[0] + d, hi[1] + h, hi[2] + d))


def bedroll(bone, name, head, foot, width=0.9, blanket="blanket", linen="linen", solid=False):
    """A bedroll on the ground: a straw-and-linen mattress, a striped blanket over it, a rolled end at the head."""
    head, foot = v3(*head), v3(*foot)
    ax = norm(foot - head)
    side = np.cross(UP, ax)
    R = np.column_stack([ax, UP, side])
    L = np.linalg.norm(foot - head)
    c = (head + foot) / 2
    add_cube(bone, name + "_mattress", c + UP * 0.08, R, (L, 0.16, width), {"all": linen, "+2": linen})
    add_cube(bone, name + "_blanket", c + ax * 0.15 + UP * 0.19, R, (L * 0.72, 0.07, width * 1.02), blanket)
    add_cube(bone, name + "_roll", head + ax * 0.22 + UP * 0.3, R, (0.42, 0.3, width * 0.94), {"all": blanket, "+1": linen, "-1": linen})
    if solid:
        lo, hi = np.minimum(head, foot), np.maximum(head, foot)
        collide((lo[0] - width / 2, lo[1], lo[2] - width / 2, hi[0] + width / 2, hi[1] + 0.3, hi[2] + width / 2))


def crate_box(bone, name, p, s=0.8, yaw=0.0, region="crate", solid=True):
    """A simple crate (used for stand-ins and small chests)."""
    p = v3(*p)
    R = gg.ry(yaw)
    add_cube(bone, name, p + UP * s / 2, R, (s, s, s), region, stretch=True)
    if solid:
        collide((p[0] - s / 2, p[1], p[2] - s / 2, p[0] + s / 2, p[1] + s, p[2] + s / 2))


def lantern(bone, name, p, size=0.3, metal="iron", chain_to=None):
    """A hanging lantern (tools/lanterns.py rebuilds the body as lit glass with posts and a ring on export) and its
    chain up to chain_to."""
    p = v3(*p)
    add_cube(bone, name, p, EYE, (size, size * 1.3, size), {"all": "lantern", "+2": metal, "-2": metal})
    if chain_to is not None:
        rope(bone, name + "_chain", p + UP * size * 0.9, chain_to, d=0.04, region=metal)


# ---------------------------------------------------------------- decoration mods' furniture
def _rot_y(x, z, yaw):
    a = math.radians(yaw)
    return x * math.cos(a) + z * math.sin(a), -x * math.sin(a) + z * math.cos(a)


class Decor:
    """Furniture of the user's decoration mods, drawn by the tent where it stands (interiors/<tent>_decor.json,
    read by InteriorDecor; EmbeddedDecor draws the installed mod's block, else `alt` (a vanilla block) if given,
    else the stand-in bone fallback_<i> of the model)."""

    def __init__(self):
        self.blocks = []

    def block(self, bid, x, y, z, facing="front", scale=1.0, glow=False, alt=None, fallback="crate", solid=True, bounds=None):
        yaw = FACING[facing] if isinstance(facing, str) else float(facing)
        b = {"block": bid, "x": x, "y": y, "z": z, "yaw": yaw, "scale": scale, "glow": glow, "alt": alt,
             "fallback_region": fallback, "bounds": bounds or BOUNDS.get(bid)}
        if b["bounds"] is None:
            raise KeyError("no model bounds known for %s: give bounds=(minX, maxX, minY, maxY, minZ, maxZ)" % bid)
        self.blocks.append(b)
        if solid:
            collide(self.footprint(b))
        return len(self.blocks) - 1

    @staticmethod
    def footprint(b):
        """Tent-local box of a block's model (bounds rotated by its yaw about the block's centre, scaled)."""
        x0, x1, y0, y1, z0, z1 = b["bounds"]
        pts = []
        for cx in (x0, x1):
            for cz in (z0, z1):
                rx, rz = _rot_y(cx - 0.5, cz - 0.5, b["yaw"])
                pts.append((rx * b["scale"], rz * b["scale"]))
        xs, zs = [p[0] for p in pts], [p[1] for p in pts]
        return (b["x"] + min(xs), b["y"] + y0 * b["scale"], b["z"] + min(zs), b["x"] + max(xs), b["y"] + y1 * b["scale"], b["z"] + max(zs))

    def fallbacks(self, root):
        """Stand-in boxes (bones fallback_<i>) drawn only when the block's mod (and its alt) are missing."""
        for i, b in enumerate(self.blocks):
            x0, y0, z0, x1, y1, z1 = self.footprint(b)
            bone = Bone("fallback_%d" % i, parent=root)
            pre = "glow" if b["glow"] else "fb"
            if b["fallback_region"] == "lantern":
                lantern(bone, "fallback_lamp_%d" % i, ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), size=max(0.2, x1 - x0))
                continue
            add_cube(bone, "%s_fallback_%d" % (pre, i), v3((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), EYE,
                     (max(0.04, x1 - x0), max(0.04, y1 - y0), max(0.04, z1 - z0)), b["fallback_region"], stretch=True)

    def write(self, path):
        data = {"blocks": [], "seats": [], "paintings": [], "switches": []}
        for i, b in enumerate(self.blocks):
            e = {"block": b["block"], "x": round(b["x"], 4), "y": round(b["y"], 4), "z": round(b["z"], 4), "yaw": b["yaw"],
                 "scale": b["scale"], "fallback": "fallback_%d" % i}
            if b["glow"]:
                e["glow"] = True
            if b["alt"]:
                e["alt"] = b["alt"]
            data["blocks"].append(e)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=1)
        return data


# ---------------------------------------------------------------- extent, icon, export
def _all_cubes(b):
    yield from b.cubes
    for ch in b.children:
        yield from _all_cubes(ch)


def extent(root, pad=0.05):
    """Tent-local box round every cube of the model (the render box and the free-area check)."""
    lo, hi = v3(1e9, 1e9, 1e9), v3(-1e9, -1e9, -1e9)
    for c in _all_cubes(root):
        R = c.bone.frame_rot() @ np.asarray(c.axes, dtype=float)
        C = c.bone.to_world(np.asarray(c.center, dtype=float))
        for sx in (-1, 1):
            for sy in (-1, 1):
                for sz in (-1, 1):
                    p = C + R @ (np.asarray(c.size) * 0.5 * v3(sx, sy, sz))
                    lo, hi = np.minimum(lo, p), np.maximum(hi, p)
    return (lo[0] - pad, max(0.0, lo[1]) - 0.0, lo[2] - pad, hi[0] + pad, hi[1] + pad, hi[2] + pad)


def write_tent_json(path, model_name, ext, colliders, decor_path):
    """tents/<tent>.json: what the Java TentType needs (extent, collision boxes, model and decor paths)."""
    data = {
        "model": "models/entity/%s.bbmodel" % model_name,
        "decor": decor_path,
        "extent": [round(float(v), 3) for v in ext],
        "colliders": [[round(float(v), 3) for v in b] for b in colliders],
    }
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=1)
    return data


def icon_aframe(path, cloth=(201, 180, 138), dark=(141, 122, 86), wood=(110, 76, 40), red=None, cone=False):
    """16x16 inventory icon: a small A-frame (or cone) tent seen from the front."""
    from PIL import Image
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    p = im.load()
    for y in range(3, 14):
        half = (y - 3) * 7 / 10
        for x in range(16):
            d = abs(x - 7.5)
            if d <= half:
                inside = d < half - 1.2 and y > 8 and not cone
                c = (60, 45, 30) if inside else cloth
                if red and (y // 2) % 2 == 0 and cone:
                    c = red
                if abs(d - half) < 0.6:
                    c = dark
                p[x, y] = c + (255,)
    for y in range(3, 15):
        p[7, y] = wood + (255,)
        p[8, y] = wood + (255,)
    for x in range(1, 15):
        p[x, 14] = (90, 70, 45, 255)
    for x in (1, 14):
        p[x, 13] = (90, 70, 45, 255)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path)


def export(root, name, decor=None, icon=None, visible_box=(8, 6, 0)):
    """Writes everything the mod needs for one tent (see the module doc). Returns the model dict."""
    tex_path = os.path.join(ASSETS, "textures/entity", tt.NAME)
    tt.make_texture(tex_path)
    with open(tex_path, "rb") as f:
        png = f.read()
    textures = [gn.texture_entry(tt.NAME, tt.SIZE, png, "entity", tt.NAME)]
    textures[0]["id"] = "0"
    if decor is not None:
        decor_path = "interiors/%s_decor.json" % name
        decor.write(os.path.join(ASSETS, decor_path))
    else:
        decor_path = None
    ext = extent(root)
    out_model = os.environ.get("TENT_OUT")
    outs = [out_model] if out_model else [os.path.join(ROOT, "blockbench/%s.bbmodel" % name),
                                          os.path.join(ASSETS, "models/entity/%s.bbmodel" % name)]
    model = gn.export(root, [], textures, outs, name=name, visible_box=visible_box)
    if not out_model:
        write_tent_json(os.path.join(ASSETS, "tents/%s.json" % name), name, ext, list(COLLIDERS),
                        "/assets/medievalships/" + decor_path if decor_path else None)
        if icon is not None:
            icon(os.path.join(ASSETS, "textures/item/%s.png" % name))
    print("%s: %d cubes, extent %s, %d collision boxes, %d mod blocks" % (
        name, len(model["elements"]), ["%.2f" % v for v in ext], len(COLLIDERS), 0 if decor is None else len(decor.blocks)))
    return model
