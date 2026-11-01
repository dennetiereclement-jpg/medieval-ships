"""Heavy cart frame helpers shared by cart_hay, cart_logs and cart_barrels (on top of cartlib).

gear(): the bed, a heavy outer frame (side raves and end beams), wheels of their own radius per axle (front wheels
smaller on a wagon), the axle blocks and a thick drawbar. iron_ring(): an iron hoop round a vertical axis (barrel
hoops). bolt(): a small iron plate (the brackets and bolt heads of the reference carts). log12(): a twelve-sided log
(three boxes turned 30 degrees, ends staggered so they do not z-fight), bark sides, ring ends.
Coordinates as in cartlib: cart-local blocks, y up, +z = front, the anchor block's centre at (0, 0, 0).
"""
import math

import numpy as np

import cartlib as cl
from cartlib import EYE, UP, X, add_cube, beam, v3


def gear(root, half_w, z0, z1, bed_y, axles, wheel_w=0.22, spokes=8, segs=14, felloe=0.18, hub_d=0.32,
         detail=None, drawbar_len=1.9, plank="plank", sill="wood_dark", gap=0.14):
    """axles = [(z, radius), ...]: one = a two-wheeled cart, two = a wagon. Wheels just outside the frame (gap)."""
    track = 2 * (half_w + wheel_w / 2 + gap)
    g = cl.Bone("gear", parent=root)
    cl.bed(g, "bed", half_w, z0, z1, bed_y, region=plank, sill=sill)
    for k, (z, R) in enumerate(axles):
        cl.wheel_pair(g, "wheel_%d" % k, z, R, track, width=wheel_w, detail=detail, spokes=spokes, segs=segs,
                      felloe=felloe, hub_d=hub_d, spoke_d=0.09)
        h = bed_y - 0.26 - R
        if h > 0.03:
            add_cube(g, "axle_block_%d" % k, (0, R + h / 2, z), EYE, (2 * half_w - 0.2, h + 0.04, 0.22), "wood_dark")
        for s in (1, -1):        # iron straps holding the axle under the frame
            add_cube(detail or g, "axle_strap_%d_%d" % (k, (s + 1) // 2), (s * (half_w - 0.05), R + 0.02, z), EYE,
                     (0.06, max(0.1, bed_y - 0.2 - R), 0.12), "iron")
    for s in (1, -1):            # outer side raves (the heavy frame along the bed edges)
        add_cube(g, "rave_%d" % ((s + 1) // 2), (s * (half_w + 0.04), bed_y - 0.08, (z0 + z1) / 2), EYE,
                 (0.12, 0.22, z1 - z0 + 0.16), {"all": "wood_dark", "+3": "end_grain", "-3": "end_grain"})
    for e, z, dz in (("b", z0, -0.05), ("f", z1, 0.05)):
        add_cube(g, "end_beam_" + e, (0, bed_y - 0.08, z + dz), EYE, (2 * half_w + 0.2, 0.22, 0.12),
                 {"all": "wood_dark", "+1": "end_grain", "-1": "end_grain"})
    if drawbar_len:
        cl.drawbar(g, "drawbar", z1 - 0.3, bed_y - 0.22, length=drawbar_len + 0.3, d=0.16, x_start=0.5, x_tip=0.17,
                   tip_y=0.45, region="wood_dark")
    return {"half_w": half_w, "z0": z0, "z1": z1, "bed_y": bed_y, "track": track, "gear": g}


def bolt(bone, name, p, normal="x", s=0.11, th=0.03):
    """A small square iron plate on a beam face (normal 'x' or 'z')."""
    size = (th, s, s) if normal == "x" else (s, s, th)
    add_cube(bone, name, p, EYE, size, "iron")


def side_bolts(bone, name, half_w, z0, z1, y, posts, heights, out=0.03):
    """Iron plates on the outside of both long fences, on every post, at the given heights above y."""
    i = 0.06
    for s in (1, -1):
        for k in range(posts):
            z = (z0 + i) + (z1 - z0 - 2 * i) * k / max(1, posts - 1)
            for j, h in enumerate(heights):
                bolt(bone, "%s_%d_%d_%d" % (name, (s + 1) // 2, k, j), (s * (half_w - i + 0.06 + out), y + h, z), "x")


def iron_ring(bone, name, center, radius, h=0.07, th=0.03, segs=12):
    """A horizontal iron hoop (polygon of segs flat segments) round a vertical axis through center."""
    c = v3(*center)
    pts = [c + v3(radius * math.cos(2 * math.pi * k / segs), 0, radius * math.sin(2 * math.pi * k / segs)) for k in range(segs)]
    for k in range(segs):
        beam(bone, "%s_%d" % (name, k), pts[k], pts[(k + 1) % segs], h, "iron", width=th, up=UP,
             extend=radius * math.tan(math.pi / segs) * 0.5 + 0.005)


def hooped_barrel(bone, hoop_bone, name, foot, r=0.46, h=1.1, staves=12, bulge=0.06, hoops=(0.1, 0.32, 0.68, 0.9),
                  solid=True, stave_region="plank"):
    """A standing barrel: `staves` bulging staves (stave_region), octagonal lids, iron hoops at the fractions `hoops`
    of its height (hoop_bone, e.g. the detail bone). Collides as one box when solid."""
    f = v3(*foot)
    w = 2 * (r + bulge * 0.5) * math.tan(math.pi / staves) * 1.05
    for k in range(staves):                      # staves: two tilted halves each (the bulge), plank texture
        a = 2 * math.pi * (k + 0.5) / staves
        rd = v3(math.cos(a), 0, math.sin(a))
        p0, pm, p1 = f + rd * r, f + UP * (h / 2) + rd * (r + bulge), f + UP * h + rd * r
        for j, (a0, a1) in enumerate(((p0, pm), (pm, p1))):
            beam(bone, "%s_stave_%d_%d" % (name, k, j), a0, a1, 0.05, stave_region, width=w, up=rd, extend=0.006)
    for j, t in enumerate((0.04, h - 0.04)):     # the lids
        for k, ang in enumerate((0.0, math.pi / 4)):
            add_cube(bone, "%s_lid_%d_%d" % (name, j, k), f + UP * (t + 0.003 * k), cl.gg.ry(ang), (2 * r * 0.92, 0.05, 2 * r * 0.92 * 0.414 + 0.01),
                     "barrel_top", stretch=True)
    add_cube(bone, "%s_lid_c" % name, f + UP * (h - 0.035), EYE, (2 * r * 0.66, 0.05, 2 * r * 0.66), "barrel_top", stretch=True)
    if solid:
        cl.collide((f[0] - r - bulge, f[1], f[2] - r - bulge, f[0] + r + bulge, f[1] + h, f[2] + r + bulge))
    for j, t in enumerate(hoops):
        rr = r + bulge * (1 - abs(2 * t - 1)) + 0.03
        iron_ring(hoop_bone, "%s_hoop_%d" % (name, j), f + UP * (t * h), rr, segs=staves)


def log12(bone, name, p0, p1, r=0.22, cap_bone=None):
    """A round log from p0 to p1: twelve-sided prism of three boxes, bark sides, ring ends."""
    p0, p1 = v3(*p0), v3(*p1)
    d = cl.norm(p1 - p0)
    L = np.linalg.norm(p1 - p0)
    e1 = cl.norm(np.cross(d, UP)) if abs(d[1]) < 0.9 else X
    e2 = np.cross(d, e1)
    for k, ang in enumerate((0.0, math.pi / 6, math.pi / 3)):
        a = e1 * math.cos(ang) + e2 * math.sin(ang)
        b = np.cross(d, a)
        add_cube(bone, "%s_%d" % (name, k), (p0 + p1) / 2, np.column_stack([d, a, b]), (L - 0.012 * k, 2 * r * 0.966, 2 * r * 0.966),
                 "bark", u_dir=d)
    for j, (p, s) in enumerate(((p0, -1), (p1, 1))):     # the ring ends: one square cap each, rings stretched over it
        add_cube(cap_bone or bone, "%s_end_%d" % (name, j), p + d * s * 0.05, np.column_stack([d, e1, e2]),
                 (0.03, 2 * r * 0.98, 2 * r * 0.98), {"all": "bark", "+1": "log_end", "-1": "log_end"}, stretch=True)


def strap(bone, name, pts, d=0.07, region="rope"):
    """A rope / strap along a polyline of points."""
    pts = [v3(*p) for p in pts]
    for k in range(len(pts) - 1):
        beam(bone, "%s_%d" % (name, k), pts[k], pts[k + 1], d, region, width=d * 1.3, extend=d * 0.45)


def bale_strings(bone, name, center, size, yaw=0.0, n=2, region="wood_dark"):
    """The strings round a hay bale (bottom centre `center`, size, yaw as cartlib.hay_bale): n thin bands across its
    long side."""
    c = v3(*center) + UP * size[1] / 2
    R = cl.gg.ry(yaw)
    along = R[:, 0] if size[0] >= size[2] else R[:, 2]
    L = max(size[0], size[2])
    for k in range(n):
        f = (k + 1) / (n + 1) - 0.5
        dims = (0.035, size[1] + 0.02, size[2] + 0.02) if size[0] >= size[2] else (size[0] + 0.02, size[1] + 0.02, 0.035)
        add_cube(bone, "%s_%d" % (name, k), c + along * f * L, R, dims, region)
