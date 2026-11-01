"""Shared helpers of the eight carts (one block each, static, drawn like the tents from a .bbmodel).

The carts reuse the tents' whole chain (tools/tents/tentlib.py: Bone, add_cube, beam, post, rope, loft, platform,
lantern, crate_box, collide, Decor, extent) with their own atlas (tools/carts/cart_texture.py -> carts.png). A cart
generator (tools/carts/generate_<cart>.py) does, in this order:

    import cartlib as cl
    cl.setup("cart_x")                        # the carts' atlas becomes the regions, collision list emptied
    root = cl.Bone("cart_x")
    gear = cl.running_gear(root, ...)         # or by hand: cl.wheel / cl.axle / cl.bed / cl.fence / cl.drawbar
    ... cl.hoop_cover / cl.roof / cl.lantern_post / cl.barrel / cl.log / cl.hay_bale / cl.produce_crate ...
    cl.collide(box)                           # extra collision boxes (x0, y0, z0, x1, y1, z1) cart-local
    cl.export(root, "cart_x", decor=None, icon=lambda p: cl.icon_cart(p, ...))

export() writes blockbench/<cart>.bbmodel, the assets copy models/entity/<cart>.bbmodel, the shared atlas
textures/entity/carts.png, the item icon textures/item/<cart>.png, (interiors/<cart>_decor.json when a Decor is given)
and carts/<cart>.json (model, texture, decor, extent, colliders) which the Java TentType reads (TentTypes.CARTS).
Coordinates: cart-local blocks, y up (y = 0 is the top of the ground block the cart stands on), +z = the cart's
front (its drawbar; it faces the player who placed it), the anchor block's centre at (0, 0, 0).

Bones: put small things (spokes, ropes, lantern arms, cargo detail) under a bone named "detail" (hidden beyond
tentDecorDistance, like the tents' detail), the rest under the root or any other bone.
"""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "tents"))
sys.path.insert(0, os.path.join(HERE, ".."))
import tentlib as tl  # noqa: E402
import cart_texture as ct  # noqa: E402

gg, gn = tl.gg, tl.gn
v3, norm, Bone, add_cube, beam = tl.v3, tl.norm, tl.Bone, tl.add_cube, tl.beam
EYE, UP, X = tl.EYE, tl.UP, np.array([1.0, 0.0, 0.0])
ASSETS, ROOT = tl.ASSETS, tl.ROOT
collide, collide_segment, post, pole, rope, loft, platform, lantern, crate_box, Decor = (
    tl.collide, tl.collide_segment, tl.post, tl.pole, tl.rope, tl.loft, tl.platform, tl.lantern, tl.crate_box, tl.Decor)
COLLIDERS = tl.COLLIDERS


def setup(name):
    """Points the shared generators at the carts' atlas; call first."""
    tl.setup(name)
    gn.REGIONS = {k: (0,) + r for k, r in ct.REGIONS.items()}
    gn.SIZE = ct.SIZE
    gg.REGIONS = dict(ct.REGIONS)
    gg.SIZE = ct.SIZE


# ---------------------------------------------------------------- wheels, axles
def wheel(bone, name, center, radius, width=0.2, spokes=10, segs=14, felloe=0.15, hub_d=0.3, hub_len=0.42,
          spoke_d=0.075, region="wood_dark", spoke_region="wood", tyre="iron", solid=True, detail=None):
    """A round spoked wheel turning about x (the axle across the cart) at `center` (touching the ground when
    center y == radius): a polygon rim of `segs` tilted felloe segments (the outer face iron when tyre is a region),
    an octagonal hub (two boxes turned 45 degrees) with iron caps, `spokes` spokes. Collides as one box."""
    c = v3(*center)
    r_mid = radius - felloe / 2
    pts = [c + v3(0, r_mid * math.cos(2 * math.pi * k / segs), r_mid * math.sin(2 * math.pi * k / segs)) for k in range(segs)]
    for k in range(segs):
        p0, p1 = pts[k], pts[(k + 1) % segs]
        mid = (p0 + p1) / 2
        d = norm(p1 - p0)
        n = np.cross(d, X)                               # beam frame: u = d, v = x (the wheel's width), n = u x v
        out = "+3" if np.dot(n, mid - c) > 0 else "-3"
        faces = {"all": region}
        if tyre:
            faces[out] = tyre
        beam(bone, "%s_rim_%d" % (name, k), p0, p1, width, faces, width=felloe, up=X, extend=felloe * math.tan(math.pi / segs) + 0.01)
    sb = detail if detail is not None else bone
    for k in range(spokes):
        a = 2 * math.pi * (k + 0.5) / spokes
        dr = v3(0, math.cos(a), math.sin(a))
        beam(sb, "%s_spoke_%d" % (name, k), c + dr * (hub_d * 0.4), c + dr * (radius - felloe * 0.8), spoke_d, spoke_region,
             width=spoke_d * 0.8, up=X)
    for k, ang in enumerate((0.0, math.pi / 4)):
        R = gg.rx(ang)
        add_cube(bone, "%s_hub_%d" % (name, k), c, R, (hub_len, hub_d, hub_d), {"all": region, "+1": "end_grain", "-1": "end_grain"})
    for s in (1, -1):
        add_cube(bone, "%s_cap_%d" % (name, (s + 1) // 2), c + X * s * (hub_len / 2 + 0.02), gg.rx(math.pi / 8),
                 (0.05, hub_d * 0.75, hub_d * 0.75), tyre or "iron")
    if solid:
        h = radius * 0.8
        collide((c[0] - width / 2 - 0.02, max(0.0, c[1] - radius), c[2] - h, c[0] + width / 2 + 0.02, c[1] + radius * 0.92, c[2] + h))


def axle(bone, name, x0, x1, y, z, d=0.14, region="wood_dark"):
    """The axle tree across the cart (x0 -> x1) at height y."""
    return beam(bone, name, (x0, y, z), (x1, y, z), d, {"all": region, "+1": "iron", "-1": "iron"})


def wheel_pair(bone, name, z, radius, track, width=0.2, axle_y=None, detail=None, **kw):
    """Two wheels at x = +-track/2 on an axle at z (wheels on the ground), and the axle between their hubs."""
    for s, sn in ((1, "r"), (-1, "l")):
        wheel(bone, "%s_%s" % (name, sn), (s * track / 2, radius, z), radius, width=width, detail=detail, **kw)
    axle(bone, name + "_axle", -track / 2, track / 2, radius if axle_y is None else axle_y, z)


# ---------------------------------------------------------------- body
def bed(bone, name, half_w, z0, z1, y, th=0.08, plank_w=0.3, region="plank", sill="wood_dark", sills=True, cross=3, solid=True):
    """The cart's floor: planks along z with their top at y, two sills (long beams) under it and `cross` cross
    members; collides as one slab."""
    platform(bone, name, -half_w, half_w, z0, z1, y, th=th, plank_w=plank_w, along="z", region=region, solid=False, joists=False)
    if sills:
        for s in (1, -1):
            add_cube(bone, "%s_sill_%d" % (name, (s + 1) // 2), (s * (half_w - 0.14), y - th - 0.09, (z0 + z1) / 2), EYE,
                     (0.16, 0.18, z1 - z0 + 0.1), {"all": sill, "+3": "end_grain", "-3": "end_grain"})
    for k in range(cross):
        z = z0 + 0.12 + (z1 - z0 - 0.24) * k / max(1, cross - 1)
        add_cube(bone, "%s_cross_%d" % (name, k), (0, y - th - 0.05, z), EYE, (2 * half_w + 0.04, 0.1, 0.14),
                 {"all": sill, "+1": "end_grain", "-1": "end_grain"})
    if solid:
        collide((-half_w, y - th - 0.18, z0, half_w, y, z1))


def fence(bone, name, p0, p1, h=0.75, posts=3, boards=(0.25, 0.55, 0.88), board_h=0.14, d=0.12, region="plank",
          post_region="wood", gap_boards=False, solid=True, top_rail=True):
    """A slatted side rail from p0 to p1 (floor points): `posts` upright posts, horizontal boards at the fractions
    `boards` of h, a top rail; collides as a thin wall of height h."""
    p0, p1 = v3(*p0), v3(*p1)
    for k in range(posts):
        p = p0 + (p1 - p0) * k / max(1, posts - 1)
        beam(bone, "%s_post_%d" % (name, k), p - UP * 0.12, p + UP * (h + 0.06), d, {"all": post_region, "+1": "end_grain", "-1": "end_grain"})
    for i, b in enumerate(boards):
        last = i == len(boards) - 1 and top_rail
        beam(bone, "%s_board_%d" % (name, i), p0 + UP * b * h, p1 + UP * b * h, board_h if not last else 0.1,
             post_region if last else region, width=0.06 if not last else d * 1.15, up=UP, extend=d * 0.5)
    if solid:
        lo, hi = np.minimum(p0, p1), np.maximum(p0, p1)
        collide((lo[0] - 0.08, lo[1], lo[2] - 0.08, hi[0] + 0.08, lo[1] + h, hi[2] + 0.08))


def box_sides(bone, name, half_w, z0, z1, y, h=0.75, front=True, back=True, **kw):
    """The four slatted sides of a cart bed (front and back optional)."""
    i = 0.06
    fence(bone, name + "_r", (half_w - i, y, z0 + i), (half_w - i, y, z1 - i), h=h, **kw)
    fence(bone, name + "_l", (-half_w + i, y, z0 + i), (-half_w + i, y, z1 - i), h=h, **kw)
    kw2 = dict(kw)
    kw2["posts"] = max(2, kw.get("posts", 3) - 1)
    if back:
        fence(bone, name + "_b", (-half_w + i, y, z0 + i), (half_w - i, y, z0 + i), h=h, **kw2)
    if front:
        fence(bone, name + "_f", (-half_w + i, y, z1 - i), (half_w - i, y, z1 - i), h=h, **kw2)


def drawbar(bone, name, z_start, y_start, length=2.0, x_start=0.45, x_tip=0.25, tip_y=0.42, d=0.14, prop=True,
            cross=True, region="wood", solid_part=0.0):
    """The shafts: two beams from under the bed front (z_start, y_start, x = +-x_start) forward and down to the tip
    (z_start + length, tip_y, +-x_tip), a crossbar near the tip, resting on a small prop post on the ground. Does
    not collide (players walk over it), except the first `solid_part` fraction of its length when > 0."""
    zt = z_start + length
    for s, sn in ((1, "r"), (-1, "l")):
        a, b = v3(s * x_start, y_start, z_start), v3(s * x_tip, tip_y, zt)
        beam(bone, "%s_%s" % (name, sn), a, b, d, {"all": region, "+1": "end_grain", "-1": "end_grain"}, up=UP, extend=0.04)
        if solid_part > 0:
            collide_segment(a, a + (b - a) * solid_part, d, segs=2)
    if cross:
        zc = zt - 0.35
        t = (zc - z_start) / length
        xc = x_start + (x_tip - x_start) * t
        yc = y_start + (tip_y - y_start) * t
        beam(bone, name + "_cross", (-xc - 0.06, yc, zc), (xc + 0.06, yc, zc), d * 0.85, "wood_dark", up=UP)
    if prop:
        add_cube(bone, name + "_prop", (0, (tip_y - d / 2) / 2, zt - 0.12), EYE, (2 * x_tip + 0.2, tip_y - d / 2, 0.16),
                 {"all": "wood_dark", "+2": "end_grain", "-2": "end_grain"})
        add_cube(bone, name + "_prop_foot", (0, 0.04, zt - 0.12), EYE, (2 * x_tip + 0.3, 0.08, 0.3), "wood_dark")


def running_gear(root, half_w, z0, z1, bed_y, axles, radius, track=None, wheel_w=0.2, spokes=10, segs=14,
                 drawbar_len=2.0, detail=None, plank="plank", sill="wood_dark"):
    """Bed + wheels + axles + drawbar of a cart in one call: the floor from z0 to z1 (top at bed_y), half width
    half_w, `axles` = list of axle z positions (one = a two-wheeled cart, two = a wagon), wheels of `radius` on the
    ground at x = +-track/2 (default just outside the bed), the drawbar from the bed front. Returns a dict with
    the main numbers (for placing the body / cargo)."""
    track = 2 * (half_w + wheel_w / 2 + 0.08) if track is None else track
    gear = Bone("gear", parent=root)
    bed(gear, "bed", half_w, z0, z1, bed_y, region=plank, sill=sill)
    for k, z in enumerate(axles):
        wheel_pair(gear, "wheel_%d" % k, z, radius, track, width=wheel_w, detail=detail, spokes=spokes, segs=segs)
        # the axle bed: a block under the sills holding the axle
        add_cube(gear, "axle_block_%d" % k, (0, (radius + bed_y - 0.26) / 2, z), EYE,
                 (2 * half_w - 0.2, max(0.08, bed_y - 0.26 - radius), 0.18), "wood_dark")
    if drawbar_len:
        drawbar(gear, "drawbar", z1 - 0.3, bed_y - 0.2, length=drawbar_len + 0.3)
    return {"half_w": half_w, "z0": z0, "z1": z1, "bed_y": bed_y, "track": track, "radius": radius, "gear": gear}


# ---------------------------------------------------------------- covers and roofs
def arch(half_w, rise, y0, s, flat=0.0):
    """Point of an arch cross-section at s in [0, 1] (s = 0 right, 1 left): a half ellipse; flat > 0 keeps the
    sides more vertical (a wagon cover's shoulders)."""
    th = math.pi * s
    c, sn = math.cos(th), math.sin(th)
    x = half_w * math.copysign(abs(c) ** (1.0 - flat * 0.6), c)
    y = y0 + rise * sn ** (1.0 - flat * 0.5)
    return x, y


def hoop_cover(bone, name, z0, z1, half_w, y0, rise, hoops=4, region="canvas", trim="trim_gold", flare=0.25, sag=0.05,
               flat=0.35, nx=8, hoop_region="wood", th=0.035, detail=None, solid=True):
    """A rounded canvas cover on hoops: a lofted arch (half width half_w, from y0 up to y0 + rise) from z0 to z1,
    the cloth sagging a little between the `hoops` wooden hoops, the two ends flared outwards (the bonnet) by
    `flare`, a trim band (region trim, None for none) along both openings. Both faces textured. Collides as the
    cover's two walls and roof (three boxes) when solid."""
    span = max(1, hoops - 1)

    def P(s, t):
        x, y = arch(half_w, rise, y0, s, flat)
        h = (y - y0) / rise
        z = z0 + (z1 - z0) * t
        z += -flare * h * (1 - t) ** 3 + flare * h * t ** 3
        frac = (t * span) % 1.0
        k = 1.0 - sag * math.sin(math.pi * frac) * h
        return v3(x * k, y0 + (y - y0) * k, z)

    loft(bone, name, P, nx, span * 2, region, th=th)
    hb = detail if detail is not None else bone
    for j in range(hoops):
        t = j / span
        pts = [P(i / nx, t) for i in range(nx + 1)]
        for i in range(nx):
            a, b = pts[i], pts[i + 1]
            inward = -norm(v3(a[0] + b[0], (a[1] + b[1]) - 2 * y0, 0))
            beam(hb, "%s_hoop_%d_%d" % (name, j, i), a + inward * 0.05, b + inward * 0.05, 0.07, hoop_region, width=0.07,
                 up=v3(0, 0, 1), extend=0.03)
    if trim:
        for e, t in (("back", 0.0), ("front", 1.0)):
            dt = 0.06 if t == 0 else -0.06

            def T(s, u, t=t, dt=dt):
                p = P(s, t + dt * u)
                out = norm(v3(p[0], p[1] - y0, 0))
                return p + out * 0.025
            loft(bone, "%s_trim_%s" % (name, e), T, nx, 1, trim, th=th * 1.2)
    if solid:
        collide((-half_w, y0, z0, -half_w + 0.15, y0 + rise * 0.7, z1))
        collide((half_w - 0.15, y0, z0, half_w, y0 + rise * 0.7, z1))
        collide((-half_w * 0.8, y0 + rise * 0.85, z0, half_w * 0.8, y0 + rise + 0.05, z1))
    return P


def roof(bone, name, half_w, z0, z1, y_eave, rise, region="red_roof", trim="gold", th=0.08, nx=6, overhang=0.15, solid=True):
    """A curved (barrel) roof from z0 to z1 over a box body: the arch from the eaves (half_w + overhang, y_eave) to
    the ridge (y_eave + rise), planks along the cart, a trim strip along both gables (region trim, None for none)."""
    hw = half_w + overhang

    def P(s, t):
        x, y = arch(hw, rise, y_eave, s, 0.0)
        return v3(x, y, z1 + overhang + (z0 - overhang - z1 - overhang) * t)

    loft(bone, name, P, nx, 2, region, th=th)
    if trim:
        for e, t in (("front", 0.0), ("back", 1.0)):
            pts = [P(i / nx, t) for i in range(nx + 1)]
            for i in range(nx):
                beam(bone, "%s_trim_%s_%d" % (name, e, i), pts[i] + UP * 0.03, pts[i + 1] + UP * 0.03, 0.07, trim, width=0.07,
                     up=v3(0, 0, 1), extend=0.03)
    if solid:
        collide((-hw, y_eave, z0 - overhang, hw, y_eave + rise + th, z1 + overhang))
    return P


def awning(bone, name, x0, x1, z0, z1, y_back, y_front, posts=True, region="stripes", sag=0.08, fringe=True, d=0.1,
           solid=True):
    """A flat cloth awning on four posts standing on the bed (y_back / y_front = its height at z0 / z1 above the
    cart-local origin), sagging a little, a scalloped valance hanging at the front."""
    def P(s, t):
        x = x0 + (x1 - x0) * s
        z = z0 + (z1 - z0) * t
        y = y_back + (y_front - y_back) * t - sag * math.sin(math.pi * s) * math.sin(math.pi * t)
        return v3(x, y, z)
    loft(bone, name, P, 4, 3, region, th=0.03)
    if fringe:
        def F(s, t):
            return P(s, 1.0) - UP * (0.22 * t) + v3(0, 0, 0.01)
        loft(bone, name + "_valance", F, 4, 1, region, th=0.03)
    return P


# ---------------------------------------------------------------- lanterns and cargo
def lantern_post(bone, name, foot, height=1.4, arm=(0.0, 0.0, 0.35), size=0.24, d=0.09, solid=False):
    """A lantern on a post: a post from foot up `height`, an arm out by `arm`, the lantern hanging under its tip."""
    foot = v3(*foot)
    top = foot + UP * height
    tip = top + v3(*arm)
    beam(bone, name + "_post", foot, top + UP * 0.05, d, {"all": "wood_dark", "+1": "end_grain", "-1": "end_grain"})
    beam(bone, name + "_arm", top - v3(*arm) * 0.15, tip, d * 0.7, "iron", up=UP)
    lantern(bone, name + "_lamp", tip - UP * (size * 0.65 + 0.12), size=size, chain_to=tip)
    if solid:
        collide((foot[0] - d, foot[1], foot[2] - d, foot[0] + d, top[1], foot[2] + d))


def barrel(bone, name, foot, r=0.36, h=0.9, staves=8, axis="y", bulge=0.05, solid=True):
    """A wooden barrel: `staves` staves (two tilted halves each, bulging by `bulge`) round the axis (y standing,
    x or z lying, foot = the centre of one end), iron hoops in the stave texture, lids at both ends."""
    foot = v3(*foot)
    ax = {"y": UP, "x": X, "z": v3(0, 0, 1)}[axis]
    e1 = X if axis != "x" else v3(0, 0, 1)
    e2 = np.cross(ax, e1)
    w = 2 * r * math.tan(math.pi / staves) * 1.04
    for k in range(staves):
        a = 2 * math.pi * k / staves
        rd = e1 * math.cos(a) + e2 * math.sin(a)
        p0, pm, p1 = foot + rd * r, foot + ax * (h / 2) + rd * (r + bulge), foot + ax * h + rd * r
        for j, (a0, a1) in enumerate(((p0, pm), (pm, p1))):
            beam(bone, "%s_stave_%d_%d" % (name, k, j), a0, a1, 0.05, "barrel", width=w, up=rd, extend=0.005)
    for j, t in enumerate((0.03, h - 0.03)):
        c = foot + ax * t
        for k, ang in enumerate((0.0, math.pi / 4)):
            R = np.column_stack([e1 * math.cos(ang) + e2 * math.sin(ang), ax, np.cross(e1 * math.cos(ang) + e2 * math.sin(ang), ax)])
            add_cube(bone, "%s_lid_%d_%d" % (name, j, k), c, R, (2 * r * 0.88, 0.05, 2 * r * 0.88 * 0.42 * 2 ** 0.5 + 0.0),
                     "barrel_top", stretch=True)
    if solid:
        lo = np.minimum(foot - (e1 + e2) * r, foot + ax * h + (e1 + e2) * r)
        hi = np.maximum(foot - (e1 + e2) * r, foot + ax * h + (e1 + e2) * r)
        collide((lo[0], lo[1], lo[2], hi[0], hi[1], hi[2]))


def log(bone, name, p0, p1, r=0.22, solid=False):
    """A round log from p0 to p1: an octagonal prism (two boxes turned 45 degrees), bark sides, ring ends."""
    p0, p1 = v3(*p0), v3(*p1)
    d = norm(p1 - p0)
    L = np.linalg.norm(p1 - p0)
    e1 = norm(np.cross(d, UP)) if abs(d[1]) < 0.9 else X
    e2 = np.cross(d, e1)
    for k, ang in enumerate((0.0, math.pi / 4)):
        a = e1 * math.cos(ang) + e2 * math.sin(ang)
        b = np.cross(d, a)
        add_cube(bone, "%s_%d" % (name, k), (p0 + p1) / 2, np.column_stack([d, a, b]), (L, 2 * r * 0.93, 2 * r * 0.93),
                 {"all": "bark", "+1": "log_end", "-1": "log_end"}, u_dir=d)
    if solid:
        lo, hi = np.minimum(p0, p1) - r, np.maximum(p0, p1) + r
        collide((lo[0], lo[1], lo[2], hi[0], hi[1], hi[2]))


def hay_bale(bone, name, center, size=(0.9, 0.5, 0.6), yaw=0.0, solid=True):
    """A hay bale (box) resting on its bottom at center (bottom centre), turned by yaw (radians) about y."""
    c = v3(*center)
    add_cube(bone, name, c + UP * size[1] / 2, gg.ry(yaw), size, {"all": "hay", "+2": "hay_top", "-2": "hay_top"}, stretch=True)
    if solid:
        hx, hz = size[0] / 2, size[2] / 2
        ex = abs(math.cos(yaw)) * hx + abs(math.sin(yaw)) * hz
        ez = abs(math.sin(yaw)) * hx + abs(math.cos(yaw)) * hz
        collide((c[0] - ex, c[1], c[2] - ez, c[0] + ex, c[1] + size[1], c[2] + ez))


def produce_crate(bone, name, foot, size=(0.6, 0.35, 0.45), produce="apples", yaw=0.0, solid=True):
    """An open crate of produce (apples, carrots, cabbage, flowers...): a crate box and a heaped top."""
    c = v3(*foot)
    R = gg.ry(yaw)
    add_cube(bone, name, c + UP * size[1] / 2, R, size, {"all": "crate", "+2": produce}, stretch=True)
    add_cube(bone, name + "_heap", c + UP * (size[1] + 0.04), R, (size[0] * 0.8, 0.1, size[2] * 0.75), produce, stretch=True)
    if solid:
        collide((c[0] - size[0] / 2, c[1], c[2] - size[2] / 2, c[0] + size[0] / 2, c[1] + size[1], c[2] + size[2] / 2))


# ---------------------------------------------------------------- icon and export
def icon_cart(path, wheels=2, body=(150, 108, 66), dark=(86, 58, 30), cover=None, cover_dark=None, trim=None, roof=None,
              cargo=None, cargo_dark=None, stripes=None, sides=True, lantern=False):
    """16x16 inventory icon: the cart seen from the side, drawbar to the right. wheels 2 (one big) or 4 (two),
    `cover` an arched canvas colour, `roof` a box house with a curved roof of that colour, `cargo` a heap colour,
    `stripes` = (red, white) an awning; every colour an (r, g, b) tuple."""
    from PIL import Image
    im = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    p = im.load()

    def put(x, y, c):
        if 0 <= x < 16 and 0 <= y < 16:
            p[x, y] = tuple(c) + (255,)

    bed_y = 9
    for x in range(1, 13):                       # bed
        put(x, bed_y, body)
        put(x, bed_y + 1, dark)
    for k in range(4):                           # drawbar
        put(12 + k, bed_y + 1 + k // 2 + (1 if k == 3 else 0), dark)
    put(15, 14, dark)
    if sides and cover is None and roof is None:
        for x in range(1, 13):
            if x in (1, 4, 8, 12):
                for y in range(bed_y - 4, bed_y):
                    put(x, y, dark)
            put(x, bed_y - 4, body)
            put(x, bed_y - 2, body)
    if cargo is not None:
        for x in range(2, 12):
            top = bed_y - 3 - (1 if 4 <= x <= 9 else 0)
            for y in range(top, bed_y):
                put(x, y, cargo if (x + y) % 3 else (cargo_dark or cargo))
    if cover is not None:
        for x in range(1, 13):
            d = abs(x - 6.5) / 6.0
            top = int(round(2 + 3.5 * d * d))
            for y in range(top, bed_y):
                c = cover if y > top else (cover_dark or cover)
                put(x, y, c)
            if trim is not None and x in (1, 12):
                for y in range(top, bed_y):
                    put(x, y, trim)
    if roof is not None:
        for x in range(2, 12):
            for y in range(4, bed_y):
                put(x, y, body if x not in (2, 11) else (trim or dark))
        for x in range(4, 7):
            put(x, 6, (240, 200, 110))
            put(x, 5, (240, 200, 110))
        for x in range(1, 13):
            d = abs(x - 6.5) / 6.0
            put(x, int(round(2 + 2 * d * d)), roof)
            put(x, int(round(2 + 2 * d * d)) + 1, roof)
    if stripes is not None:
        for x in (2, 11):
            for y in range(3, bed_y):
                put(x, y, dark)
        for x in range(1, 13):
            put(x, 3, stripes[(x // 2) % 2])
            put(x, 4, stripes[(x // 2) % 2])
    if lantern:
        put(13, 5, dark)
        put(13, 6, (255, 210, 110))
        put(13, 7, (255, 210, 110))

    def wheel_px(cx, cy, r):
        for y in range(16):
            for x in range(16):
                d = math.hypot(x - cx, y - cy)
                if r - 1.0 <= d <= r + 0.3:
                    put(x, y, (58, 40, 22))
                elif d < r - 1 and (abs(x - cx) < 0.6 or abs(y - cy) < 0.6 or abs(abs(x - cx) - abs(y - cy)) < 0.6):
                    put(x, y, (110, 80, 46))
        put(int(cx), int(cy), (60, 60, 64))

    if wheels == 2:
        wheel_px(6.5, 11.5, 3.8)
    else:
        wheel_px(3.5, 12.5, 2.8)
        wheel_px(10.0, 12.5, 2.8)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path)


def export(root, name, decor=None, icon=None, visible_box=(8, 5, 0)):
    """Writes everything the mod needs for one cart (see the module doc). Returns the model dict."""
    tex_path = os.path.join(ASSETS, "textures/entity", ct.NAME)
    out_model = os.environ.get("CART_OUT") or os.environ.get("TENT_OUT")
    if not out_model:
        ct.make_texture(tex_path)
    else:
        tex_path = os.path.join(os.path.dirname(out_model), ct.NAME)
        ct.make_texture(tex_path)
    with open(tex_path, "rb") as f:
        png = f.read()
    textures = [gn.texture_entry(ct.NAME, ct.SIZE, png, "entity", ct.NAME)]
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
        data = tl.write_tent_json(os.path.join(ASSETS, "carts/%s.json" % name), name, ext, list(COLLIDERS),
                                  "/assets/medievalships/" + decor_path if decor_path else None)
        data["texture"] = "textures/entity/" + ct.NAME
        import json
        with open(os.path.join(ASSETS, "carts/%s.json" % name), "w") as f:
            json.dump(data, f, indent=1)
        if icon is not None:
            icon(os.path.join(ASSETS, "textures/item/%s.png" % name))
    print("%s: %d cubes, extent %s, %d collision boxes" % (name, len(model["elements"]), ["%.2f" % v for v in ext], len(COLLIDERS)))
    return model
