"""Shared helpers of the four workshops of agent A (blacksmith, leatherworker, tailor, engineer): one block each,
static, drawn like the tents and carts from a .bbmodel.

The workshops reuse the tents' and carts' chain (tools/tents/tentlib.py: Bone, add_cube, beam, post, rope, loft,
lantern, collide, Decor, extent; tools/carts/cartlib.py: barrel, lantern_post...) with their own atlas
(tools/workshops/ws_texture_a.py -> textures/entity/workshops_a.png). A generator
(tools/workshops/generate_<id>.py) does, in this order:

    import wslib_a as wl
    wl.setup("workshop_x")                     # the atlas becomes the regions, collision list emptied
    root = wl.Bone("workshop_x"); detail = wl.Bone("detail", parent=root)
    ... wl.post / wl.plank_roof / wl.stone_box / wl.table / wl.crate / wl.chain / wl.anvil / wl.gear_wheel ...
    wl.collide(box)                            # (x0, y0, z0, x1, y1, z1) workshop-local
    wl.export(root, "workshop_x", icon=fn, particles=[wl.particle("flame", (x, y, z), 0.4)])

export() writes blockbench/<id>.bbmodel, the assets copy models/entity/<id>.bbmodel, the atlas, the item icon
textures/item/<id>.png and workshops/<id>.json (model, texture, decor, extent, colliders, particles) read by the Java
TentType (group "workshops"). Coordinates: workshop-local blocks, y up (y = 0 = top of the ground block), +z = the
front (the side the player stands at to work), the anchor block's centre at (0, 0, 0): it sits inside the main
bench / forge at the front centre. Small things go under the bone named "detail" (hidden far away). Cubes whose name
starts with "glow" are drawn full bright (fire, embers, lit glass); the lanterns are rebuilt lit on export.
"""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "tents"))
sys.path.insert(0, os.path.join(HERE, "..", "carts"))
sys.path.insert(0, os.path.join(HERE, ".."))
import tentlib as tl  # noqa: E402
import cartlib as cl  # noqa: E402
import ws_texture_a as wt  # noqa: E402

gg, gn = tl.gg, tl.gn
v3, norm, Bone, add_cube, beam = tl.v3, tl.norm, tl.Bone, tl.add_cube, tl.beam
EYE, UP, X, Z = tl.EYE, tl.UP, np.array([1.0, 0.0, 0.0]), np.array([0.0, 0.0, 1.0])
ASSETS, ROOT = tl.ASSETS, tl.ROOT
collide, collide_segment, post, pole, rope, loft, lantern, Decor = (
    tl.collide, tl.collide_segment, tl.post, tl.pole, tl.rope, tl.loft, tl.lantern, tl.Decor)
COLLIDERS = tl.COLLIDERS
ry = gg.ry


def setup(name):
    """Points the shared generators at this atlas; call first."""
    tl.setup(name)
    gn.REGIONS = {k: (0,) + r for k, r in wt.REGIONS.items()}
    gn.SIZE = wt.SIZE
    gg.REGIONS = dict(wt.REGIONS)
    gg.SIZE = wt.SIZE


def particle(kind, pos, chance=0.3, count=1):
    return {"type": kind, "pos": [round(float(c), 3) for c in pos], "chance": chance, "count": count}


# ---------------------------------------------------------------- boxes
def box(bone, name, lo, hi, region, solid=False, stretch=False, u_dir=None):
    """An axis-aligned box from lo to hi (workshop-local); collides when solid."""
    lo, hi = v3(*lo), v3(*hi)
    c = add_cube(bone, name, (lo + hi) / 2, EYE, hi - lo, region, stretch=stretch, u_dir=u_dir)
    if solid:
        collide((lo[0], lo[1], lo[2], hi[0], hi[1], hi[2]))
    return c


def rbox(bone, name, foot, size, yaw, region, solid=False, stretch=False):
    """A box standing on `foot` (bottom centre), turned by yaw (radians) about y."""
    foot = v3(*foot)
    c = add_cube(bone, name, foot + UP * size[1] / 2, ry(yaw), size, region, stretch=stretch)
    if solid:
        hx, hz = size[0] / 2, size[2] / 2
        ex = abs(math.cos(yaw)) * hx + abs(math.sin(yaw)) * hz
        ez = abs(math.sin(yaw)) * hx + abs(math.cos(yaw)) * hz
        collide((foot[0] - ex, foot[1], foot[2] - ez, foot[0] + ex, foot[1] + size[1], foot[2] + ez))
    return c


def stone_box(bone, name, lo, hi, region="stone", top="stone_top", solid=True):
    """Masonry block: stone bricks on the sides (16 px a block), a slab top."""
    return box(bone, name, lo, hi, {"all": region, "+2": top or region}, solid=solid)


def octo(bone, name, p0, p1, r, region, end=None, solid=False):
    """A round bar from p0 to p1 (octagonal: two boxes turned 45 degrees), `end` region on its two ends."""
    p0, p1 = v3(*p0), v3(*p1)
    d = norm(p1 - p0)
    L = np.linalg.norm(p1 - p0)
    e1 = norm(np.cross(d, UP)) if abs(d[1]) < 0.9 else X
    e2 = np.cross(d, e1)
    for k, ang in enumerate((0.0, math.pi / 4)):
        a = e1 * math.cos(ang) + e2 * math.sin(ang)
        b = np.cross(d, a)
        add_cube(bone, "%s_%d" % (name, k), (p0 + p1) / 2, np.column_stack([d, a, b]), (L, 2 * r * 0.93, 2 * r * 0.93),
                 {"all": region, "+1": end or region, "-1": end or region}, u_dir=d)
    if solid:
        lo, hi = np.minimum(p0, p1) - r, np.maximum(p0, p1) + r
        collide((lo[0], lo[1], lo[2], hi[0], hi[1], hi[2]))


def plate(bone, name, center, normal, up, w, h, region, th=0.02, edge=None):
    """A thin flat thing (a sheet, a gear, a chain link) with `region` on both faces, edges `edge` (None: none)."""
    n = norm(v3(*normal))
    upv = v3(*up)
    upv = norm(upv - np.dot(upv, n) * n)
    u = np.cross(upv, n)
    axes = np.column_stack([u, upv, n])
    return add_cube(bone, name, center, axes, (w, h, th), {"all": edge, "+3": region, "-3": region}, stretch=True,
                    u_dir=u, v_dir=-upv)


# ---------------------------------------------------------------- structure
def plank_roof(bone, name, x0, x1, z0, z1, y_back, y_front, th=0.12, plank_w=0.36, region="plank", stagger=0.12,
               fascia="wood_dark", layer2=True, solid=True):
    """A thick plank roof sloping from the back (z0, top at y_back) to the front (z1, y_front): planks running
    front to back, their ends staggered, a second shorter layer on top (the stepped look of the pictures) and a
    fascia beam along the front and back edges."""
    n = max(1, int(round((x1 - x0) / plank_w)))
    w = (x1 - x0) / n
    slope = (y_front - y_back) / (z1 - z0)
    ang = math.atan(slope)
    R = gg.rx(-ang)
    L = (z1 - z0) / math.cos(ang)
    for k in range(n):
        xa = x0 + (k + 0.5) * w
        dz = stagger * ((k * 7) % 3) / 2.0
        zc = (z0 + z1) / 2 + dz / 2 - stagger / 2
        yc = y_back + slope * (zc - z0) - th / 2
        add_cube(bone, "%s_%d" % (name, k), (xa, yc + (0.02 if k % 2 else 0.0), zc), R, (w * 0.98, th, L - dz), region,
                 u_dir=v3(0, 0, 1))
    if layer2:
        n2 = max(1, n - 2)
        w2 = (x1 - x0 - 2 * w) / n2
        for k in range(n2):
            xa = x0 + w + (k + 0.5) * w2
            dz = 0.1 * ((k * 5) % 3)
            zc = (z0 + z1) / 2 - 0.1 + dz / 2
            yc = y_back + slope * (zc - z0) + th / 2 - 0.01
            add_cube(bone, "%s_top_%d" % (name, k), (xa, yc, zc), R, (w2 * 0.98, th * 0.9, L - 0.45 - dz), region,
                     u_dir=v3(0, 0, 1))
    if fascia:
        for e, z, y in (("f", z1, y_front), ("b", z0, y_back)):
            # a tall fascia board under the plank ends (the thick roof edge of the pictures)
            zz = z - (0.09 if e == "f" else -0.09)
            beam(bone, "%s_fascia_%s" % (name, e), (x0 - 0.04, y - th - 0.11, zz), (x1 + 0.04, y - th - 0.11, zz), 0.26,
                 {"all": fascia, "+1": "end_grain", "-1": "end_grain"}, width=0.14)
    if solid:
        collide((x0, min(y_back, y_front) - th - 0.14, z0, x1, max(y_back, y_front), z1))


def bracket(bone, name, post_pt, beam_pt, d=0.12, region="wood"):
    """A diagonal knee brace from a post to a beam."""
    return beam(bone, name, post_pt, beam_pt, d, region, extend=0.03)


def table(bone, name, x0, x1, z0, z1, h, top="plank", leg="wood", top_th=0.1, leg_d=0.14, stretcher=True, shelf=False,
          overhang=0.06, solid=True, legs_inset=0.08):
    """A sturdy bench: thick top, four square legs, stretchers low down (and a slatted shelf when shelf)."""
    add_cube(bone, name + "_top", ((x0 + x1) / 2, h - top_th / 2, (z0 + z1) / 2), EYE, (x1 - x0, top_th, z1 - z0),
             {"all": top, "+1": "end_grain", "-1": "end_grain"}, u_dir=X)
    xa, xb, za, zb = x0 + overhang + legs_inset, x1 - overhang - legs_inset, z0 + overhang + legs_inset, z1 - overhang - legs_inset
    for i, (x, z) in enumerate(((xa, za), (xb, za), (xa, zb), (xb, zb))):
        beam(bone, "%s_leg_%d" % (name, i), (x, 0.0, z), (x, h - top_th, z), leg_d, {"all": leg, "+1": "end_grain", "-1": "end_grain"})
    # apron under the top
    for e, z in (("f", zb), ("b", za)):
        beam(bone, "%s_apron_%s" % (name, e), (xa, h - top_th - 0.07, z), (xb, h - top_th - 0.07, z), 0.12, leg, width=0.06, up=UP)
    if stretcher:
        for e, x in (("l", xa), ("r", xb)):
            beam(bone, "%s_str_%s" % (name, e), (x, 0.18, za), (x, 0.18, zb), 0.09, leg, up=UP)
        beam(bone, name + "_str_mid", (xa, 0.2, (za + zb) / 2), (xb, 0.2, (za + zb) / 2), 0.09, leg, up=UP)
    if shelf:
        add_cube(bone, name + "_shelf", ((xa + xb) / 2, 0.28, (za + zb) / 2), EYE, (xb - xa + 0.1, 0.05, zb - za + 0.1), "plank",
                 u_dir=X)
    if solid:
        collide((x0, 0.0, z0, x1, h, z1))


def shelf_rack(bone, name, x0, x1, z0, z1, levels, h, region="plank", post_region="wood", back=None, solid=True):
    """An open rack: four posts and plank shelves at the heights `levels`, an optional back panel."""
    for i, (x, z) in enumerate(((x0, z0), (x1, z0), (x0, z1), (x1, z1))):
        beam(bone, "%s_post_%d" % (name, i), (x, 0.0, z), (x, h, z), 0.12, {"all": post_region, "+1": "end_grain", "-1": "end_grain"})
    for k, y in enumerate(levels):
        add_cube(bone, "%s_shelf_%d" % (name, k), ((x0 + x1) / 2, y - 0.03, (z0 + z1) / 2), EYE, (x1 - x0 + 0.1, 0.06, z1 - z0 + 0.04),
                 {"all": region, "+1": "end_grain", "-1": "end_grain"}, u_dir=X)
    if back:
        add_cube(bone, name + "_back", ((x0 + x1) / 2, h / 2, z0 - 0.02), EYE, (x1 - x0, h, 0.04), back, u_dir=X)
    if solid:
        collide((x0 - 0.06, 0.0, z0 - 0.06, x1 + 0.06, h, z1 + 0.06))


# ---------------------------------------------------------------- furniture
def crate(bone, name, foot, size=(0.8, 0.8, 0.8), yaw=0.0, region="crate", top="crate_top", solid=True, lid=False):
    """An iron-banded crate (the band texture is stretched over each face)."""
    c = rbox(bone, name, foot, size, yaw, {"all": region, "+2": top, "-2": top}, solid=solid, stretch=True)
    if lid:
        rbox(bone, name + "_lid", v3(*foot) + UP * size[1], (size[0] + 0.04, 0.06, size[2] + 0.04), yaw, {"all": "iron", "+2": top},
             stretch=True)
    return c


def chest(bone, name, foot, size=(0.9, 0.55, 0.6), yaw=0.0, solid=True, detail=None):
    """An iron-banded chest: the body (lock plate on the front), a domed lid (two tilted boards and a flat top)."""
    foot = v3(*foot)
    R = ry(yaw)
    sx, sy, sz = size
    add_cube(bone, name, foot + UP * sy / 2, R, size, {"all": "crate", "+3": "chest", "+2": "crate_top", "-2": "crate_top"}, stretch=True)
    lid_h = 0.14
    add_cube(bone, name + "_lid", foot + UP * (sy + lid_h / 2), R, (sx + 0.03, lid_h, sz * 0.7), {"all": "crate", "+2": "crate_top"}, stretch=True)
    for s in (1, -1):
        c = foot + UP * (sy + lid_h * 0.35) + R @ v3(0, 0, s * sz * 0.38)
        add_cube(bone, "%s_lid_%d" % (name, (s + 1) // 2), c, R @ gg.rx(-s * 0.55), (sx + 0.03, 0.08, sz * 0.22), "crate", stretch=True)
    b = detail if detail is not None else bone
    for k, x in enumerate((-sx * 0.33, sx * 0.33)):
        add_cube(b, "%s_band_%d" % (name, k), foot + UP * (sy + lid_h / 2 - 0.01) + R @ v3(x, 0, 0), R, (0.06, lid_h + 0.02, sz * 0.72), "iron")
    if solid:
        hx, hz = sx / 2, sz / 2
        ex = abs(math.cos(yaw)) * hx + abs(math.sin(yaw)) * hz
        ez = abs(math.sin(yaw)) * hx + abs(math.cos(yaw)) * hz
        collide((foot[0] - ex, foot[1], foot[2] - ez, foot[0] + ex, foot[1] + sy + lid_h, foot[2] + ez))


def barrel(bone, name, foot, r=0.34, h=0.85, staves=8, solid=True):
    """A standing barrel (cartlib's barrel with this atlas's staves)."""
    cl.barrel(bone, name, foot, r=r, h=h, staves=staves, solid=solid)


def tub(bone, name, foot, r=0.42, h=0.6, staves=10, solid=True, handles=True):
    """A wooden water tub: staves, two iron hoops, water a little below the rim, two taller staves as handles."""
    foot = v3(*foot)
    w = 2 * r * math.tan(math.pi / staves) * 1.06
    for k in range(staves):
        a = 2 * math.pi * k / staves
        rd = v3(math.cos(a), 0, math.sin(a))
        tall = handles and k in (0, staves // 2)
        top = h + (0.14 if tall else 0.0)
        beam(bone, "%s_stave_%d" % (name, k), foot + rd * (r * 0.94), foot + rd * r + UP * top, 0.05, "barrel", width=w, up=rd, extend=0.0)
    for j, y in enumerate((0.12, h - 0.1)):
        for k in range(staves):
            a0, a1 = 2 * math.pi * k / staves, 2 * math.pi * (k + 1) / staves
            p0 = foot + v3(math.cos(a0), 0, math.sin(a0)) * (r + 0.03) + UP * y
            p1 = foot + v3(math.cos(a1), 0, math.sin(a1)) * (r + 0.03) + UP * y
            beam(bone, "%s_hoop_%d_%d" % (name, j, k), p0, p1, 0.05, "iron", width=0.015, up=UP, extend=0.012)
    for k, ang in enumerate((0.0, math.pi / 4)):
        add_cube(bone, "%s_water_%d" % (name, k), foot + UP * (h - 0.08), ry(ang), (2 * r * 0.9, 0.04, 2 * r * 0.9 * 0.42), "water",
                 stretch=True)
        add_cube(bone, "%s_water_b%d" % (name, k), foot + UP * (h - 0.08), ry(ang + math.pi / 2), (2 * r * 0.9, 0.039, 2 * r * 0.9 * 0.42),
                 "water", stretch=True)
    add_cube(bone, name + "_bottom", foot + UP * 0.03, EYE, (2 * r * 0.95, 0.06, 2 * r * 0.95), "barrel_top", stretch=True)
    if solid:
        collide((foot[0] - r, 0.0, foot[2] - r, foot[0] + r, h, foot[2] + r))


def chain(bone, name, top, length, link=0.2, w=0.13, region="chain", hook=True):
    """A hanging chain: links alternating face-on and edge-on down from `top`, an iron hook at the bottom."""
    top = v3(*top)
    n = max(2, int(length / (link * 0.72)))
    for k in range(n):
        c = top - UP * (link * 0.5 + k * link * 0.72)
        nrm = X if k % 2 == 0 else Z
        plate(bone, "%s_link_%d" % (name, k), c, nrm, UP, w, link, region, th=0.015)
    if hook:
        b = top - UP * (link * 0.5 + n * link * 0.72)
        beam(bone, name + "_hook_a", b + UP * 0.03, b - UP * 0.08, 0.025, "iron")
        beam(bone, name + "_hook_b", b - UP * 0.08, b - UP * 0.08 + X * 0.06, 0.025, "iron", extend=0.012)
        beam(bone, name + "_hook_c", b - UP * 0.08 + X * 0.06, b - UP * 0.03 + X * 0.06, 0.025, "iron")


def hanging_lantern(bone, name, anchor, drop=0.35, size=0.3, arm=None):
    """A lantern hanging under `anchor` (on a chain); arm = a point on a post: an iron arm from it to the anchor."""
    anchor = v3(*anchor)
    if arm is not None:
        a = v3(*arm)
        beam(bone, name + "_arm", a, anchor + (anchor - a) * 0.08, 0.05, "iron", up=UP)
        beam(bone, name + "_brace", a - UP * 0.22, a + (anchor - a) * 0.55, 0.035, "iron", up=UP)
    lantern(bone, name, anchor - UP * (drop + size * 0.65), size=size, chain_to=anchor)


def standing_lantern(bone, name, foot, size=0.28):
    """A lantern standing on a table (its body; the export rebuilds it lit with posts, cap and ring)."""
    foot = v3(*foot)
    lantern(bone, name, foot + UP * (size * 0.65 + 0.03), size=size)


def candle(bone, name, foot, h=0.14, r=0.035, holder=True):
    foot = v3(*foot)
    if holder:
        add_cube(bone, name + "_dish", foot + UP * 0.012, EYE, (0.12, 0.024, 0.12), "brass")
    add_cube(bone, name, foot + UP * (0.024 + h / 2), EYE, (2 * r, h, 2 * r), "candle")
    add_cube(bone, "glow_" + name + "_flame", foot + UP * (0.024 + h + 0.03), ry(0.785), (0.025, 0.05, 0.025), "flame")


def anvil(bone, name, foot, yaw=0.0, s=1.0, detail=None, solid=True):
    """A black iron anvil standing on `foot`: a wide stepped foot, a narrow waist, the face with a square heel and
    a tapering horn (towards +x of its frame)."""
    foot = v3(*foot)
    R = ry(yaw)

    def b(nm, c, size, reg="black_iron", rot=None, bn=None):
        add_cube(bn or bone, "%s_%s" % (name, nm), foot + R @ (v3(*c) * s), R if rot is None else R @ rot, v3(*size) * s,
                 {"all": reg, "+2": "steel"} if nm == "face" else reg)
    b("base", (0, 0.06, 0), (0.62, 0.12, 0.44))
    b("base2", (0, 0.16, 0), (0.48, 0.09, 0.34))
    b("waist", (0, 0.29, 0), (0.28, 0.18, 0.24))
    b("neck", (0, 0.41, 0), (0.42, 0.07, 0.3))
    b("face", (-0.04, 0.5, 0), (0.62, 0.12, 0.34))
    b("heel", (-0.38, 0.5, 0), (0.14, 0.1, 0.26))
    b("horn_0", (0.34, 0.5, 0), (0.12, 0.1, 0.24))
    b("horn_1", (0.45, 0.505, 0), (0.12, 0.08, 0.17))
    b("horn_2", (0.55, 0.515, 0), (0.1, 0.06, 0.1))
    b("horn_3", (0.62, 0.52, 0), (0.07, 0.04, 0.05))
    b("hardy", (-0.25, 0.565, 0.0), (0.05, 0.02, 0.05), "iron", bn=detail)
    if solid:
        pts = [foot + R @ v3(x, 0, z) * s for x in (-0.45, 0.68) for z in (-0.22, 0.22)]
        lo, hi = np.min(pts, axis=0), np.max(pts, axis=0)
        collide((lo[0], foot[1], lo[2], hi[0], foot[1] + 0.56 * s, hi[2]))


def hammer(bone, name, p, direction, length=0.36, head="iron", lying=True):
    """A hammer from its handle end p along `direction`, head across at the far end."""
    p, d = v3(*p), norm(v3(*direction))
    tip = p + d * length
    beam(bone, name + "_handle", p, tip, 0.035, "wood", up=UP)
    side = norm(np.cross(d, UP)) if lying else norm(np.cross(d, X if abs(d[0]) < 0.9 else Z))
    if lying:
        side = UP if abs(d[1]) > 0.9 else norm(np.cross(d, UP))
    beam(bone, name + "_head", tip - side * 0.08, tip + side * 0.07, 0.065, head, up=d if abs(np.dot(d, UP)) < 0.9 else X)


def tongs(bone, name, p, direction, length=0.5):
    p, d = v3(*p), norm(v3(*direction))
    side = norm(np.cross(d, UP)) if abs(d[1]) < 0.9 else X
    beam(bone, name + "_a", p + side * 0.02, p + d * length - side * 0.015, 0.022, "iron", up=UP)
    beam(bone, name + "_b", p - side * 0.02, p + d * length + side * 0.015, 0.022, "iron", up=UP)
    beam(bone, name + "_jaw", p + d * length - side * 0.03, p + d * (length + 0.05) + side * 0.03, 0.03, "iron", up=UP)


def knife(bone, name, p, direction, length=0.22):
    p, d = v3(*p), norm(v3(*direction))
    beam(bone, name + "_grip", p, p + d * length * 0.45, 0.03, "wood_dark", up=UP)
    beam(bone, name + "_blade", p + d * length * 0.45, p + d * length, 0.01, "steel", width=0.04, up=UP)


def ingot(bone, name, foot, yaw=0.0, region="ingot"):
    rbox(bone, name, foot, (0.18, 0.05, 0.08), yaw, {"all": region}, stretch=True)


def cloth_roll(bone, name, p0, p1, r, region, end_region):
    """A roll of cloth lying from p0 to p1 (octagonal prism, the spiral on the ends)."""
    octo(bone, name, p0, p1, r, region, end=end_region)


def hanging_cloth(bone, name, a, b, length, region, sway=0.03, nx=3, ny=3, th=0.02):
    """A cloth hanging from the bar a-b (its top edge) straight down by `length`, soft folds across."""
    a, b = v3(*a), v3(*b)
    side = norm(b - a)
    out = norm(np.cross(side, UP))

    def P(s, t):
        p = a + (b - a) * s - UP * (length * t)
        return p + out * (sway * math.sin(s * math.pi * 3.0) * t + 0.01 * math.sin(s * 9))
    loft(bone, name, P, nx, ny, region, th=th)


def draped(bone, name, x0, x1, z_back, z_edge, y_top, hang, region, out_dir=1, nx=3, th=0.02, curl=0.04):
    """A cloth lying on a table top (x0..x1, from z_back to the edge z_edge at y_top) and hanging over the edge by
    `hang` (out_dir = +1: over a +z edge, -1: over a -z edge). The region spans the whole cloth."""
    flat = abs(z_edge - z_back)
    total = flat + hang

    def P(s, t):
        x = x0 + (x1 - x0) * s
        d = t * total
        if d <= flat:
            return v3(x, y_top + 0.012, z_back + out_dir * d)
        dd = d - flat
        return v3(x, y_top + 0.012 - dd, z_edge + out_dir * (0.025 + curl * math.sin(s * math.pi * 2) * dd / hang))
    loft(bone, name, P, nx, 4, region, th=th)


def gear_wheel(bone, name, center, r, normal=(0, 0, 1), teeth=12, spokes=6, th=0.12, region="wood", tooth_region="wood_dark",
               hub_region="iron", rim=0.12, segs=None, detail=None):
    """A big wooden gear wheel (real 3D): a polygon rim, `teeth` teeth outside, `spokes` spokes, an iron hub."""
    c = v3(*center)
    n = norm(v3(*normal))
    e1 = norm(np.cross(n, UP)) if abs(n[1]) < 0.9 else X
    e2 = np.cross(n, e1)
    segs = segs or max(12, teeth)
    rm = r - rim / 2
    pts = [c + (e1 * math.cos(2 * math.pi * k / segs) + e2 * math.sin(2 * math.pi * k / segs)) * rm for k in range(segs)]
    for k in range(segs):
        p0, p1 = pts[k], pts[(k + 1) % segs]
        beam(bone, "%s_rim_%d" % (name, k), p0, p1, rim, region, width=th, up=n, extend=rim * math.tan(math.pi / segs) + 0.01)
    tb = detail if detail is not None else bone
    for k in range(teeth):
        a = 2 * math.pi * (k + 0.5) / teeth
        rd = e1 * math.cos(a) + e2 * math.sin(a)
        beam(tb, "%s_tooth_%d" % (name, k), c + rd * (r - 0.02), c + rd * (r + 0.1), 0.1, tooth_region, width=th * 0.9, up=n)
    for k in range(spokes):
        a = 2 * math.pi * k / spokes
        rd = e1 * math.cos(a) + e2 * math.sin(a)
        beam(bone, "%s_spoke_%d" % (name, k), c + rd * 0.08, c + rd * (rm - rim * 0.3), 0.08, region, width=th * 0.8, up=n)
    for k, ang in enumerate((0.0, math.pi / 4)):
        a = e1 * math.cos(ang) + e2 * math.sin(ang)
        b = np.cross(n, a)
        add_cube(bone, "%s_hub_%d" % (name, k), c, np.column_stack([a, b, n]), (0.22, 0.22, th + 0.06), hub_region)
    add_cube(tb, name + "_axle", c + n * (th / 2 + 0.05), np.column_stack([e1, e2, n]), (0.08, 0.08, 0.1), "brass")


def small_gear(bone, name, center, r, normal=(0, 1, 0), region="gear", th=0.03, up=None):
    """A small brass gear (flat plate with the gear texture, transparent between the teeth)."""
    n = norm(v3(*normal))
    if up is None:
        up = X if abs(n[1]) > 0.9 else UP
    return plate(bone, name, center, n, up, 2 * r, 2 * r, region, th=th, edge=None)


def pipe(bone, name, pts, r=0.045, region="copper", joints=True):
    """A copper pipe through the points, a ring at each bend."""
    pts = [v3(*p) for p in pts]
    for k in range(len(pts) - 1):
        octo(bone, "%s_%d" % (name, k), pts[k], pts[k + 1], r, region)
    if joints:
        for k, p in enumerate(pts[1:-1]):
            add_cube(bone, "%s_joint_%d" % (name, k), p, EYE, (2.6 * r, 2.6 * r, 2.6 * r), "brass")


def sack(bone, name, foot, size=(0.4, 0.5, 0.36), yaw=0.0, region="sack", solid=False):
    foot = v3(*foot)
    R = ry(yaw)
    sx, sy, sz = size
    # a bulging body (octagonal, wider in the middle), the gathered top, the tied neck and its tuft
    for k, (y0, y1, f) in enumerate(((0.0, 0.18, 0.82), (0.18, 0.6, 1.0), (0.6, 0.78, 0.78))):
        for j, ang in enumerate((0.0, math.pi / 4)):
            add_cube(bone, "%s_%d_%d" % (name, k, j), foot + UP * sy * (y0 + y1) / 2, R @ ry(ang),
                     (sx * f * 0.93, sy * (y1 - y0), sz * f * 0.93), region, stretch=True)
    add_cube(bone, name + "_top", foot + UP * sy * 0.84, R @ ry(0.4), (sx * 0.42, sy * 0.12, sz * 0.42), region, stretch=True)
    add_cube(bone, name + "_neck", foot + UP * sy * 0.91, R, (sx * 0.24, sy * 0.06, sz * 0.24), "rope")
    add_cube(bone, name + "_tuft", foot + UP * sy * 0.97, R @ ry(0.7), (sx * 0.34, sy * 0.08, sz * 0.3), region, stretch=True)
    if solid:
        collide((foot[0] - sx / 2, foot[1], foot[2] - sz / 2, foot[0] + sx / 2, foot[1] + sy, foot[2] + sz / 2))


# ---------------------------------------------------------------- export
def write_json(name, ext, colliders, decor_path, particles):
    data = {
        "model": "models/entity/%s.bbmodel" % name,
        "texture": "textures/entity/" + wt.NAME,
        "decor": decor_path,
        "extent": [round(float(v), 3) for v in ext],
        # (post boxes start half a thickness under their foot: nothing collides below the ground)
        "colliders": [[round(float(v), 3) for v in (b[0], max(0.0, b[1]), b[2], b[3], b[4], b[5])] for b in colliders],
        "particles": particles or [],
    }
    path = os.path.join(ASSETS, "workshops/%s.json" % name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=1)
    return data


def export(root, name, decor=None, icon=None, particles=None, visible_box=(8, 5, 0)):
    """Writes everything the mod needs for one workshop (see the module doc). Returns the model dict.
    WS_OUT=<file>: writes only the model there (previews)."""
    out_model = os.environ.get("WS_OUT")
    tex_path = os.path.join(ASSETS, "textures/entity", wt.NAME) if not out_model else os.path.join(os.path.dirname(out_model), wt.NAME)
    wt.make_texture(tex_path)
    with open(tex_path, "rb") as f:
        png = f.read()
    textures = [gn.texture_entry(wt.NAME, wt.SIZE, png, "entity", wt.NAME)]
    textures[0]["id"] = "0"
    decor_path = None
    if decor is not None and decor.blocks:
        decor_path = "interiors/%s_decor.json" % name
        if not out_model:
            decor.write(os.path.join(ASSETS, decor_path))
    ext = tl.extent(root)
    outs = [out_model] if out_model else [os.path.join(ROOT, "blockbench/%s.bbmodel" % name),
                                          os.path.join(ASSETS, "models/entity/%s.bbmodel" % name)]
    model = gn.export(root, [], textures, outs, name=name, visible_box=visible_box)
    if not out_model:
        write_json(name, ext, list(COLLIDERS), "/assets/medievalships/" + decor_path if decor_path else None, particles)
        if icon is not None:
            path = os.path.join(ASSETS, "textures/item/%s.png" % name)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            icon(path)
    print("%s: %d cubes, extent %s, %d collision boxes" % (name, len(model["elements"]), ["%.2f" % v for v in ext], len(COLLIDERS)))
    return model


# ---------------------------------------------------------------- icons
def icon_canvas():
    from PIL import Image
    return Image.new("RGBA", (16, 16), (0, 0, 0, 0))


def icon_draw(im, rows, palette):
    """Pixel art: rows = 16 strings of 16 chars, palette = {char: (r, g, b)} ('.' transparent)."""
    p = im.load()
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch in palette:
                p[x, y] = tuple(palette[ch]) + (255,)
    return im
