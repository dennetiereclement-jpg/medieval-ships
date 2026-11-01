"""Shared helpers of the workshops of agent B (the cook, the alchemist, the enchanter): one block each, static,
drawn like the tents and carts from a .bbmodel.

They reuse the tents' and carts' whole chain (tools/tents/tentlib.py: Bone, add_cube, beam, post, rope, loft,
platform, lantern, collide, extent; tools/carts/cartlib.py: barrel, log) with their own atlas
(tools/workshops/ws_texture_b.py -> textures/entity/workshops_b.png). A generator
(tools/workshops/generate_<id>.py) does, in this order:

    import wslib_b as wl
    wl.setup("workshop_x")                    # the atlas becomes the regions, collision list emptied
    root = wl.Bone("workshop_x")
    detail = wl.Bone("detail", parent=root)   # small props: hidden beyond tentDecorDistance (only ONE bone "detail")
    ... wl.stone_block / wl.plank_roof / wl.table / wl.shelf / wl.book_row / wl.bottle / wl.crystal_cluster ...
    wl.collide(box)                           # extra collision boxes (x0, y0, z0, x1, y1, z1) workshop-local
    wl.export(root, "workshop_x", particles=[...], icon=fn)

export() writes blockbench/<id>.bbmodel, the assets copy models/entity/<id>.bbmodel, the atlas
textures/entity/workshops_b.png, the item icon textures/item/<id>.png and workshops/<id>.json (model, texture,
decor, extent, colliders, particles) which the Java side reads. Coordinates: workshop-local blocks, y up (y = 0 is
the top of the ground block), +z = the front (the side the player works from; it faces the player who placed it),
the anchor block's centre at (0, 0, 0). Elements named glow_* are drawn full bright (fire, candle flames, potions,
crystals, the enchanting book); lantern bodies are rebuilt as lit lanterns by tools/lanterns.py on export.
WS_OUT=<file>: write only the model there (previews), nothing else.
"""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "carts"))
sys.path.insert(0, os.path.join(HERE, "..", "tents"))
sys.path.insert(0, os.path.join(HERE, ".."))
import tentlib as tl  # noqa: E402
import cartlib as cl  # noqa: E402
import ws_texture_b as wt  # noqa: E402

gg, gn = tl.gg, tl.gn
v3, norm, Bone, add_cube, beam = tl.v3, tl.norm, tl.Bone, tl.add_cube, tl.beam
EYE, UP = tl.EYE, tl.UP
X, Z = np.array([1.0, 0.0, 0.0]), np.array([0.0, 0.0, 1.0])
ASSETS, ROOT = tl.ASSETS, tl.ROOT
collide, collide_segment, post, pole, rope, loft, platform, lantern = (
    tl.collide, tl.collide_segment, tl.post, tl.pole, tl.rope, tl.loft, tl.platform, tl.lantern)
barrel, log = cl.barrel, cl.log
COLLIDERS = tl.COLLIDERS
ry = gg.ry


def setup(name):
    """Points the shared generators at the atlas of agent B; call first."""
    tl.setup(name)
    gn.REGIONS = {k: (0,) + r for k, r in wt.REGIONS.items()}
    gn.SIZE = wt.SIZE
    gg.REGIONS = dict(wt.REGIONS)
    gg.SIZE = wt.SIZE


# ---------------------------------------------------------------- basic shapes
def box(bone, name, lo, hi, region, yaw=0.0, **kw):
    """An axis-aligned (or turned by yaw radians about y round its centre) box from corner lo to corner hi."""
    lo, hi = v3(*lo), v3(*hi)
    return add_cube(bone, name, (lo + hi) / 2, ry(yaw), np.abs(hi - lo), region, **kw)


def octo(bone, name, foot, r, h, region, k=0.83, **kw):
    """A round-ish upright body (two boxes, the second turned 45 degrees and a little smaller): foot = bottom centre."""
    foot = v3(*foot)
    c = foot + UP * h / 2
    a = add_cube(bone, name, c, EYE, (2 * r, h, 2 * r), region, **kw)
    b = add_cube(bone, name + "_r", c, ry(math.pi / 4), (2 * r * k, h * 0.999, 2 * r * k), region, **kw)
    return a, b


def plate(bone, name, center, w, h, region, normal=(0, 0, 1), up=(0, 1, 0), th=0.02, both=True, back=None, **kw):
    """A thin plate (sign, banner, rug, picture) of size w x h facing `normal`; the region stretched on its face."""
    n = norm(v3(*normal))
    upv = v3(*up)
    upv = norm(upv - np.dot(upv, n) * n)
    side = np.cross(upv, n)
    axes = np.column_stack([side, upv, n])
    regs = {"all": back or None, "+3": region}
    if both:
        regs["-3"] = region if back is None else back
    return add_cube(bone, name, center, axes, (w, h, th), regs, stretch=True, u_dir=side, v_dir=-upv, **kw)


# ---------------------------------------------------------------- masonry and woodwork
def stone_block(bone, name, lo, hi, region="stone_bricks", top="stone_slab", course=0.5, relief=0.03, solid=True, seed=0):
    """A masonry block from lo to hi made of courses of `course` height, each course set in or out a little (a rough
    stone face), the top course capped with `top` (None: same region)."""
    lo, hi = v3(*lo), v3(*hi)
    H = hi[1] - lo[1]
    n = max(1, int(round(H / course)))
    ch = H / n
    for k in range(n):
        d = relief * (((k * 7 + seed * 3) % 3) - 1)
        y0 = lo[1] + k * ch
        regs = {"all": region}
        if k == n - 1 and top:
            regs["+2"] = top
        add_cube(bone, "%s_%d" % (name, k), ((lo[0] + hi[0]) / 2, y0 + ch / 2, (lo[2] + hi[2]) / 2), EYE,
                 (hi[0] - lo[0] + 2 * d, ch + (0.002 if k < n - 1 else 0), hi[2] - lo[2] + 2 * d), regs)
    if solid:
        collide((lo[0], lo[1], lo[2], hi[0], hi[1], hi[2]))


def plank_roof(bone, name, x0, x1, z0, z1, y_back, y_front, th=0.16, plank_w=0.45, region="plank", rng=None,
               beams=True, beam_region="wood_dark", ragged=0.14, solid=False, along="z"):
    """A sloping roof of thick planks running front to back (z0 back, z1 front; height y_back / y_front at their
    top), ragged ends (each plank a little longer or shorter), each plank tilted a hair, and under it two beams
    across (front and back) when beams."""
    import random
    rng = rng or random.Random(7)
    if along == "x":
        # boards across the roof (left to right), lapped from the back down to the front like a shed roof, their
        # ends ragged at both sides, a few short boards patched in
        n = max(1, int(round((z1 - z0) / plank_w)))
        w = (z1 - z0) / n
        for k in range(n):
            z = z0 + (k + 0.5) * w
            y = y_back + (y_front - y_back) * (k + 0.5) / n
            jl, jr = rng.uniform(-ragged * 0.4, ragged), rng.uniform(-ragged * 0.4, ragged)
            dy = rng.uniform(-0.02, 0.03) + (0.03 if k % 2 else 0.0)
            tilt = math.atan2(y_back - y_front, z1 - z0)
            R = gg.rx(tilt)
            add_cube(bone, "%s_%d" % (name, k), ((x0 - jl + x1 + jr) / 2, y - th / 2 + dy, z), R, (x1 + jr - x0 + jl, th, w * 1.04),
                     {"all": region, "+1": "end_grain", "-1": "end_grain"}, u_dir=X)
    else:
        n = max(1, int(round((x1 - x0) / plank_w)))
        w = (x1 - x0) / n
        for k in range(n):
            x = x0 + (k + 0.5) * w
            jb, jf = rng.uniform(-ragged, ragged * 0.4), rng.uniform(-ragged * 0.5, ragged)
            dy = rng.uniform(-0.025, 0.025)
            p0 = v3(x, y_back - th / 2 + dy, z0 - jb)
            p1 = v3(x, y_front - th / 2 + dy, z1 + jf)
            beam(bone, "%s_%d" % (name, k), p0, p1, th, {"all": region, "+1": "end_grain", "-1": "end_grain"}, width=w * 0.96, up=UP,
                 u_dir=norm(p1 - p0))
    if beams:
        for e, z, y in (("b", z0 + 0.25, y_back), ("f", z1 - 0.25, y_front)):
            yy = y - th - 0.11
            beam(bone, "%s_beam_%s" % (name, e), (x0 - 0.18, yy, z), (x1 + 0.18, yy, z), 0.22, {"all": beam_region, "+1": "end_grain", "-1": "end_grain"},
                 width=0.2, up=UP)
        if along == "x":   # rafters front to back under the boards
            for k in range(4):
                x = x0 + 0.3 + (x1 - x0 - 0.6) * k / 3
                beam(bone, "%s_rafter_%d" % (name, k), (x, y_back - th - 0.08, z0 + 0.05), (x, y_front - th - 0.08, z1 - 0.05), 0.16,
                     {"all": beam_region, "+1": "end_grain", "-1": "end_grain"}, width=0.16, up=UP)
    if solid:
        collide((x0, min(y_back, y_front) - th, z0, x1, max(y_back, y_front), z1))


def table(bone, name, x0, x1, z0, z1, top_y, top_th=0.1, leg=0.12, top_region="plank", leg_region="wood",
          shelf_y=None, apron=True, solid=True, legs_inset=0.06, detail=None):
    """A sturdy table: a plank top (planks along x) with its upper face at top_y, four square legs, aprons under the
    top, an optional lower shelf at shelf_y; collides as one box."""
    platform(bone, name + "_top", x0, x1, z0, z1, top_y, th=top_th, plank_w=0.33, along="x", region=top_region, solid=False, joists=False)
    i = legs_inset + leg / 2
    for k, (x, z) in enumerate(((x0 + i, z0 + i), (x1 - i, z0 + i), (x0 + i, z1 - i), (x1 - i, z1 - i))):
        add_cube(bone, "%s_leg_%d" % (name, k), (x, (top_y - top_th) / 2, z), EYE, (leg, top_y - top_th, leg),
                 {"all": leg_region, "+2": "end_grain", "-2": "end_grain"})
    if apron:
        for k, z in enumerate((z0 + i, z1 - i)):
            beam(bone, "%s_apron_%d" % (name, k), (x0 + i, top_y - top_th - 0.08, z), (x1 - i, top_y - top_th - 0.08, z), 0.14,
                 "wood_dark", width=0.06, up=UP)
        for k, x in enumerate((x0 + i, x1 - i)):
            beam(bone, "%s_apron_s_%d" % (name, k), (x, top_y - top_th - 0.08, z0 + i), (x, top_y - top_th - 0.08, z1 - i), 0.14,
                 "wood_dark", width=0.06, up=UP)
    if shelf_y is not None:
        platform(bone, name + "_shelf", x0 + i - leg / 2, x1 - i + leg / 2, z0 + i - leg / 2, z1 - i + leg / 2, shelf_y, th=0.06,
                 plank_w=0.3, along="x", region="plank_dark", solid=False, joists=False)
    if solid:
        collide((x0, 0.0, z0, x1, top_y, z1))


def shelf(bone, name, x0, x1, z_back, y, depth=0.32, th=0.06, region="plank", brackets=2, bracket_region="wood_dark"):
    """A wall shelf: one board (top face at y) from x0 to x1 against a wall at z_back, with brackets under it."""
    add_cube(bone, name, ((x0 + x1) / 2, y - th / 2, z_back + depth / 2), EYE, (x1 - x0, th, depth),
             {"all": region, "+1": "end_grain", "-1": "end_grain"}, u_dir=X)
    for k in range(brackets):
        x = x0 + 0.12 + (x1 - x0 - 0.24) * (k / max(1, brackets - 1) if brackets > 1 else 0.5)
        beam(bone, "%s_br_%d" % (name, k), (x, y - th - 0.3, z_back + 0.02), (x, y - th - 0.01, z_back + depth * 0.8), 0.06,
             bracket_region, width=0.06, up=X)


# ---------------------------------------------------------------- books and writing
BOOK_COLORS = ("red", "blue", "green", "purple", "brown", "teal", "yellow")


def book(bone, name, foot, w, h, d, color, yaw=0.0, tilt=0.0, glow=False):
    """A standing book: thickness w (x), height h, depth d (z), spine to the front (+z), pages on top; tilt (radians)
    leans it about z (to the side); foot = bottom centre."""
    foot = v3(*foot)
    R = ry(yaw) @ gg.rz(tilt)
    c = foot + R @ v3(0, h / 2, 0)
    reg = "book_" + color
    return add_cube(bone, ("glow_" if glow else "") + name, c, R, (w, h, d), {"all": reg, "+2": "book_top", "-2": "book_top"},
                    stretch=True)


def book_flat(bone, name, foot, w, th, d, color, yaw=0.0):
    """A book lying flat (cover up), spine to the front; foot = bottom centre."""
    foot = v3(*foot)
    reg = "book_" + color
    return add_cube(bone, name, foot + UP * th / 2, ry(yaw), (w, th, d), {"all": "book_top", "+2": reg, "-2": reg, "+3": reg},
                    stretch=True)


def book_row(bone, name, x0, x1, y, z_front, depth, rng, colors=BOOK_COLORS, hmin=0.24, hmax=0.36, wmin=0.07, wmax=0.11,
             gap=0.12, lean_end=True):
    """A row of standing books on a shelf (top face at y) from x0 to x1, spines at z_front; random heights and
    colours, now and then a gap, the last book leaning on its neighbour."""
    x = x0 + 0.02
    k = 0
    while x < x1 - wmin:
        w = rng.uniform(wmin, wmax)
        if x + w > x1:
            break
        if k > 1 and rng.random() < gap:
            x += rng.uniform(0.05, 0.12)
            k += 1
            continue
        h = rng.uniform(hmin, hmax)
        d = depth * rng.uniform(0.8, 1.0)
        book(bone, "%s_%d" % (name, k), (x + w / 2, y, z_front - d / 2), w, h, d, rng.choice(colors))
        x += w + 0.005
        k += 1
    if lean_end and x < x1 - 0.12:
        h = hmax * 0.95
        tilt = -0.42
        w = 0.08
        book(bone, "%s_lean" % name, (x + 0.05 + h * math.sin(-tilt) / 2, y, z_front - depth * 0.45), w, h, depth * 0.9,
             rng.choice(colors), tilt=tilt)


def book_stack(bone, name, foot, n, rng, w=0.32, d=0.24, th=0.075, colors=BOOK_COLORS, yaw=0.0):
    foot = v3(*foot)
    y = 0.0
    for k in range(n):
        ww, dd = w * rng.uniform(0.82, 1.0), d * rng.uniform(0.85, 1.0)
        t = th * rng.uniform(0.85, 1.25)
        book_flat(bone, "%s_%d" % (name, k), foot + UP * y + v3(rng.uniform(-0.02, 0.02), 0, rng.uniform(-0.02, 0.02)), ww, t, dd,
                  rng.choice(colors), yaw=yaw + rng.uniform(-0.25, 0.25))
        y += t
    return y


def open_book(bone, name, c, w=0.5, d=0.36, yaw=0.0, cover="book_purple", glow=True, lift=0.0, tilt=0.0):
    """An open book lying on a surface at c (centre, on the surface): the cover, two page blocks forming a shallow
    V (the pages region, its halves), lit when glow (the enchanting book)."""
    c = v3(*c) + UP * (lift + d / 2 * math.sin(tilt))
    R = ry(yaw) @ gg.rx(tilt)
    add_cube(bone, name + "_cover", c + R @ v3(0, 0.015, 0), R, (w + 0.05, 0.03, d + 0.04), cover, stretch=True)
    pre = "glow_" if glow else ""
    for s, sub in ((-1, (0.0, 0.0, 0.5, 1.0)), (1, (0.5, 0.0, 1.0, 1.0))):
        Rp = R @ gg.rz(s * 0.16)
        pc = c + R @ v3(s * w / 4, 0.03 + 0.025 + w / 4 * math.sin(0.16), 0)
        cube = add_cube(bone, "%s%s_page_%d" % (pre, name, (s + 1) // 2), pc, Rp, (w / 2, 0.05, d), {"all": "book_top", "+2": "pages"},
                        stretch=True)
        if cube.faces.get("up"):
            cube.faces["up"]["sub"] = sub


def parchment(bone, name, c, w=0.3, d=0.4, yaw=0.0, curl=True):
    c = v3(*c)
    add_cube(bone, name, c + UP * 0.006, ry(yaw), (w, 0.012, d), {"all": "parchment"}, stretch=True)
    if curl:
        R = ry(yaw)
        add_cube(bone, name + "_roll", c + R @ v3(0, 0.03, -d / 2), R, (w * 1.02, 0.06, 0.06), {"all": "parchment"}, stretch=True)


def quill_ink(bone, name, foot, yaw=0.0):
    """An ink pot with a quill standing in it (the feather two crossed cut-out planes)."""
    foot = v3(*foot)
    octo(bone, name + "_pot", foot, 0.06, 0.09, {"all": "ink", "+2": "iron_dark"})
    tip = foot + UP * 0.06
    top = tip + ry(yaw) @ v3(0.08, 0.42, -0.05)
    d = norm(top - tip)
    mid = (tip + top) / 2
    side = norm(np.cross(d, Z if abs(d[2]) < 0.9 else X))
    for k, ax in enumerate((side, norm(np.cross(d, side)))):
        n = np.cross(ax, d)
        axes = np.column_stack([ax, d, n])
        add_cube(bone, "%s_quill_%d" % (name, k), mid, axes, (0.14, np.linalg.norm(top - tip), 0.004),
                 {"all": None, "+3": "quill", "-3": "quill"}, stretch=True, u_dir=ax, v_dir=-d)


# ---------------------------------------------------------------- bottles, crystals, candles
def bottle(bone, name, foot, color, r=0.07, h=0.17, neck_h=0.07, shape="round", glow=True, cork=True):
    """A potion bottle: body (round: two boxes, tall: one; flask: a wide low body), a glass neck, a cork. The body
    is lit (glow) by default."""
    foot = v3(*foot)
    reg = "potion_" + color
    pre = "glow_" if glow else ""
    if shape == "tall":
        add_cube(bone, pre + name, foot + UP * h / 2, EYE, (2 * r, h, 2 * r), {"all": reg}, stretch=True)
    else:
        if shape == "flask":
            h = h * 0.75
            r = r * 1.25
        octo(bone, pre + name, foot, r, h, {"all": reg}, stretch=True)
    add_cube(bone, name + "_neck", foot + UP * (h + neck_h / 2), EYE, (r * 0.75, neck_h, r * 0.75), "glass", stretch=True)
    if cork:
        add_cube(bone, name + "_cork", foot + UP * (h + neck_h + 0.02), EYE, (r * 0.85, 0.04, r * 0.85), "cork", stretch=True)


def crystal_cluster(bone, name, foot, color, rng, n=5, h=0.5, w=0.11, spread=0.11, glow=True, lean=0.32):
    """A cluster of crystals (lit): a tall central prism and smaller ones leaning out round it, each a square prism
    turned 45 degrees with a narrower tip."""
    foot = v3(*foot)
    reg = "crystal_" + color
    pre = "glow_" if glow else ""
    for k in range(n):
        if k == 0:
            off, hh, ww, tilt = v3(0, 0, 0), h, w, v3(0, 0, 0)
        else:
            a = 2 * math.pi * (k - 1) / (n - 1) + rng.uniform(-0.4, 0.4)
            off = v3(math.cos(a), 0, math.sin(a)) * spread * rng.uniform(0.7, 1.1)
            hh, ww = h * rng.uniform(0.4, 0.7), w * rng.uniform(0.6, 0.85)
            tilt = norm(off) * lean
        d = norm(UP + tilt)
        b = foot + off
        t = b + d * hh * 0.8
        beam(bone, "%s%s_%d" % (pre, name, k), b - d * 0.02, t, ww, {"all": reg}, width=ww, up=v3(1, 0, 1), stretch=True)
        beam(bone, "%s%s_%d_tip" % (pre, name, k), t - d * 0.01, t + d * hh * 0.2, ww * 0.55, {"all": reg}, width=ww * 0.55,
             up=v3(1, 0, 1), stretch=True)


def candle(bone, name, foot, h=0.22, r=0.045, holder="brass", flame=True):
    """A candle (wax, wick, lit flame) on a small holder plate."""
    foot = v3(*foot)
    y = 0.0
    if holder:
        add_cube(bone, name + "_holder", foot + UP * 0.015, EYE, (r * 3.2, 0.03, r * 3.2), holder)
        y = 0.03
    add_cube(bone, name, foot + UP * (y + h / 2), EYE, (2 * r, h, 2 * r), {"all": "wax"}, stretch=True)
    # a drip of wax on one side
    add_cube(bone, name + "_drip", foot + v3(r, y + h * 0.7, 0), EYE, (0.02, h * 0.3, 0.03), "wax")
    if flame:
        add_cube(bone, "glow_" + name + "_flame", foot + UP * (y + h + 0.05), ry(math.pi / 4), (0.045, 0.085, 0.045), "flame", stretch=True)


# ---------------------------------------------------------------- hanging things
def crossed(bone, name, center, w, h, region, glow=False, yaw=0.0):
    """Two crossed cut-out planes (plants, flames, bunches) of size w x h centred at center."""
    center = v3(*center)
    pre = "glow_" if glow else ""
    for k, a in enumerate((yaw + math.pi / 4, yaw - math.pi / 4)):
        R = ry(a)
        add_cube(bone, "%s%s_%d" % (pre, name, k), center, R, (w, h, 0.004), {"all": None, "+3": region, "-3": region}, stretch=True,
                 u_dir=R[:, 0], v_dir=-UP)


def hanging_bunch(bone, name, top, kind, length=0.6, width=0.3, string=0.0):
    """A bunch (herbs, garlic, peppers) hanging from `top` on a string of `string` length."""
    top = v3(*top)
    if string > 0:
        beam(bone, name + "_string", top, top - UP * (string + 0.04), 0.02, "rope")
    crossed(bone, name, top - UP * (string + length / 2), width, length, kind)


def vine(bone, name, top, length, width, normal=(0, 0, 1), region="vines", sway=0.0):
    """A hanging strip of vines / ivy (a cut-out plane, both faces) from `top`, facing `normal`."""
    top = v3(*top)
    n = norm(v3(*normal))
    c = top - UP * length / 2 + n * sway
    plate(bone, name, c, width, length, region, normal=n, th=0.004)


def chain(bone, name, p0, p1, link=0.07):
    """An iron chain: alternating links (small boxes, every second one turned 90 degrees about the chain)."""
    p0, p1 = v3(*p0), v3(*p1)
    L = np.linalg.norm(p1 - p0)
    n = max(1, int(L / link))
    d = (p1 - p0) / n
    for k in range(n):
        a, b = p0 + d * k, p0 + d * (k + 1)
        up = X if k % 2 == 0 else Z
        beam(bone, "%s_%d" % (name, k), a, b + d * 0.15, 0.035, "iron_dark", width=0.012, up=up)


# ---------------------------------------------------------------- containers and cookware
def chest(bone, name, foot, w=0.8, h=0.6, d=0.55, yaw=0.0, solid=True):
    """An iron-banded chest: body (front with the lock plate to +z turned by yaw) and a lid a little wider."""
    foot = v3(*foot)
    R = ry(yaw)
    hb = h * 0.66
    add_cube(bone, name, foot + UP * hb / 2, R, (w, hb, d), {"all": "chest_side", "+3": "chest_front", "+1": "chest_side"}, stretch=True)
    add_cube(bone, name + "_lid", foot + UP * (hb + (h - hb) / 2), R, (w + 0.03, h - hb, d + 0.03),
             {"all": "chest_side", "+2": "chest_top", "+3": "chest_side"}, stretch=True)
    for s in (-1, 1):
        add_cube(bone, "%s_strap_%d" % (name, (s + 1) // 2), foot + R @ v3(s * w * 0.3, h / 2 + 0.005, 0), R, (0.05, h + 0.02, d + 0.05),
                 "iron")
    if solid:
        ex = abs(math.cos(yaw)) * w / 2 + abs(math.sin(yaw)) * d / 2
        ez = abs(math.sin(yaw)) * w / 2 + abs(math.cos(yaw)) * d / 2
        collide((foot[0] - ex, foot[1], foot[2] - ez, foot[0] + ex, foot[1] + h, foot[2] + ez))


def crate(bone, name, foot, s=0.6, yaw=0.0, solid=True, straps=True):
    foot = v3(*foot)
    R = ry(yaw)
    add_cube(bone, name, foot + UP * s / 2, R, (s, s, s), "crate", stretch=True)
    if straps:
        for k in (-1, 1):
            add_cube(bone, "%s_strap_%d" % (name, k), foot + R @ v3(k * s * 0.33, s / 2, 0), R, (0.05, s + 0.02, s + 0.02), "iron")
    if solid:
        e = s / 2 * (abs(math.cos(yaw)) + abs(math.sin(yaw)))
        collide((foot[0] - e, foot[1], foot[2] - e, foot[0] + e, foot[1] + s, foot[2] + e))


def sack(bone, name, foot, s=0.42, yaw=0.0, region="sack"):
    foot = v3(*foot)
    R = ry(yaw)
    add_cube(bone, name, foot + UP * s * 0.5, R, (s, s, s * 0.82), region, stretch=True)
    add_cube(bone, name + "_top", foot + UP * s * 1.08, R, (s * 0.7, s * 0.2, s * 0.6), region, stretch=True)
    add_cube(bone, name + "_neck", foot + UP * s * 1.24, R, (s * 0.3, s * 0.14, s * 0.3), region, stretch=True)
    add_cube(bone, name + "_tie", foot + UP * s * 1.2, R, (s * 0.34, 0.04, s * 0.34), "rope")


def jar(bone, name, foot, r=0.08, h=0.2, region="jar"):
    foot = v3(*foot)
    octo(bone, name, foot, r, h, {"all": region, "+2": "jar_top"}, stretch=True)
    add_cube(bone, name + "_lid", foot + UP * (h + 0.02), EYE, (r * 1.5, 0.04, r * 1.5), {"all": "linen"}, stretch=True)


def bowl(bone, name, foot, r=0.17, h=0.08, content=None, region="bowl"):
    foot = v3(*foot)
    octo(bone, name, foot, r, h, {"all": region, "+2": content or region})
    add_cube(bone, name + "_base", foot + UP * 0.01, EYE, (r * 1.2, 0.02, r * 1.2), region)


def apple(bone, name, c, s=0.11, color="apple"):
    c = v3(*c)
    add_cube(bone, name, c + UP * s / 2, ry(0.3), (s, s * 0.95, s), color, stretch=True)
    add_cube(bone, name + "_stem", c + UP * (s + 0.02), EYE, (0.015, 0.04, 0.015), "wood_dark")


def bread(bone, name, c, yaw=0.0, l=0.3, w=0.16, h=0.1):
    c = v3(*c)
    R = ry(yaw)
    add_cube(bone, name, c + UP * h * 0.35, R, (l, h * 0.7, w), {"all": "bread", "+2": "bread_top"}, stretch=True)
    add_cube(bone, name + "_top", c + UP * h * 0.8, R, (l * 0.8, h * 0.35, w * 0.75), {"all": "bread", "+2": "bread_top"}, stretch=True)


def cauldron(bone, name, foot, r=0.45, h=0.55, content="stew", legs=True, bail_to=None, glow_content=False, detail=None):
    """A black iron cauldron: 8 staves bulging out (barrel-like), a thick rim, a bottom, three stubby legs, the content
    surface inside and a bail (handle) rising to `bail_to` when given."""
    foot = v3(*foot)
    staves = 8
    bulge = r * 0.16
    w = 2 * (r + bulge) * math.tan(math.pi / staves) * 1.04
    lift = 0.1 if legs else 0.0
    base = foot + UP * lift
    for k in range(staves):
        a = 2 * math.pi * (k + 0.5) / staves
        rd = v3(math.cos(a), 0, math.sin(a))
        prof = (base + rd * (r * 0.62), base + UP * (h * 0.3) + rd * (r + bulge), base + UP * (h * 0.68) + rd * (r + bulge * 0.9),
                base + UP * h + rd * (r * 0.84))
        for j in range(3):
            beam(bone, "%s_stave_%d_%d" % (name, k, j), prof[j], prof[j + 1], 0.06, "cauldron", width=w * 1.08, up=rd, extend=0.025)
    # the rim: an octagon of thick bars
    for k in range(staves):
        a0, a1 = 2 * math.pi * k / staves, 2 * math.pi * (k + 1) / staves
        q0 = base + UP * (h + 0.02) + v3(math.cos(a0), 0, math.sin(a0)) * r * 0.84
        q1 = base + UP * (h + 0.02) + v3(math.cos(a1), 0, math.sin(a1)) * r * 0.84
        beam(bone, "%s_lip_%d" % (name, k), q0, q1, 0.07, "iron_dark", width=0.09, up=UP, extend=0.03)
    octo(bone, name + "_bottom", base - UP * 0.02, r * 0.75, 0.06, "cauldron")
    pre = "glow_" if glow_content else ""
    octo(bone, pre + name + "_content", base + UP * (h - 0.1), r * 0.86, 0.04, {"all": content}, stretch=True)
    if legs:
        for k in range(3):
            a = 2 * math.pi * k / 3 + 0.3
            p = foot + v3(math.cos(a), 0, math.sin(a)) * r * 0.55
            add_cube(bone, "%s_leg_%d" % (name, k), p + UP * 0.07, EYE, (0.08, 0.14, 0.08), "iron_dark")
    # ear lugs and the bail
    for s in (-1, 1):
        add_cube(bone, "%s_ear_%d" % (name, (s + 1) // 2), base + UP * (h - 0.02) + X * s * (r * 0.84 + 0.06), EYE, (0.06, 0.1, 0.08), "iron_dark")
    if bail_to is not None:
        top = v3(*bail_to)
        db = detail if detail is not None else bone
        pts = []
        for k in range(7):
            t = k / 6
            a = math.pi * t
            pts.append(base + UP * h + X * (-math.cos(a) * (r * 0.84 + 0.08)) + UP * (math.sin(a) * (top[1] - base[1] - h)))
        for k in range(6):
            beam(db, "%s_bail_%d" % (name, k), pts[k], pts[k + 1], 0.035, "iron_dark", width=0.035, extend=0.015)


def fire(bone, name, c, s=0.55, logs=3, flames=True):
    """A wood fire on a hearth at c (its foot centre): crossed logs, glowing embers, crossed flames (lit)."""
    c = v3(*c)
    for k in range(logs):
        a = math.pi * k / logs + 0.3
        d = v3(math.cos(a), 0, math.sin(a)) * s * 0.48
        log(bone, "%s_log_%d" % (name, k), c - d + UP * (0.07 + 0.05 * (k % 2)), c + d + UP * (0.07 + 0.05 * (k % 2)), r=0.065)
    add_cube(bone, "glow_%s_embers" % name, c + UP * 0.025, EYE, (s * 0.85, 0.05, s * 0.85), {"all": "embers"}, stretch=True)
    for k in range(4):
        a = 2 * math.pi * k / 4 + 0.5
        add_cube(bone, "glow_%s_coal_%d" % (name, k), c + v3(math.cos(a), 0, math.sin(a)) * s * 0.33 + UP * 0.05, ry(a),
                 (0.09, 0.07, 0.08), {"all": "embers"}, stretch=True)
    if flames:
        crossed(bone, name + "_flame", c + UP * (0.08 + s * 0.42), s * 0.8, s * 0.85, "fire", glow=True)
        crossed(bone, name + "_flame_b", c + UP * (0.06 + s * 0.3) + v3(0.05, 0, -0.04), s * 0.55, s * 0.6, "fire", glow=True, yaw=0.4)


def mortar(bone, name, foot, r=0.14, h=0.12):
    foot = v3(*foot)
    octo(bone, name, foot, r, h, {"all": "stone_slab", "+2": "cobble"})
    add_cube(bone, name + "_base", foot + UP * 0.015, EYE, (r * 1.5, 0.03, r * 1.5), "stone_slab")
    p0 = foot + UP * (h * 0.6)
    p1 = p0 + v3(0.12, 0.2, -0.05)
    beam(bone, name + "_pestle", p0, p1, 0.05, {"all": "stone_slab"}, width=0.05)


def banner(bone, name, top_center, w, h, region, normal=(0, 0, 1), rod=True, wave=0.035, rod_region="wood_dark",
           knobs="gold"):
    """A hanging banner (both faces textured, cut-out V bottom) from a rod: top_center = middle of its top edge."""
    top = v3(*top_center)
    n = norm(v3(*normal))
    side = norm(np.cross(UP, n))

    def P(s, t):
        return top + side * ((s - 0.5) * w) - UP * (h * t) + n * (wave * math.sin(math.pi * t) * (0.6 + 0.4 * math.sin(math.pi * s)))
    loft(bone, name, P, 1, 3, region, th=0.02, u_hint=side, v_hint=-UP)
    if rod:
        a, b = top - side * (w / 2 + 0.1) + n * 0.01 + UP * 0.03, top + side * (w / 2 + 0.1) + n * 0.01 + UP * 0.03
        beam(bone, name + "_rod", a, b, 0.05, rod_region, width=0.05)
        if knobs:
            for k, p in enumerate((a, b)):
                add_cube(bone, "%s_knob_%d" % (name, k), p, EYE, (0.08, 0.08, 0.08), knobs)


def rug(bone, name, x0, x1, z0, z1, y, region="rug", th=0.025, sub=None):
    c = add_cube(bone, name, ((x0 + x1) / 2, y + th / 2, (z0 + z1) / 2), EYE, (x1 - x0, th, z1 - z0),
                 {"all": "purple_paint", "+2": region}, stretch=True, u_dir=X, v_dir=Z)
    if sub is not None and c.faces.get("up"):
        c.faces["up"]["sub"] = sub
    return c


# ---------------------------------------------------------------- export
def export(root, name, particles=(), icon=None, decor=None, visible_box=(10, 6, 0)):
    """Writes everything the mod needs for one workshop (see the module doc). Returns the model dict."""
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
        data = {
            "model": "models/entity/%s.bbmodel" % name,
            "texture": "textures/entity/" + wt.NAME,
            "decor": ("/assets/medievalships/" + decor_path) if decor_path else None,
            "extent": [round(float(v), 3) for v in ext],
            "colliders": [[round(float(v if i != 1 else max(0.0, v)), 3) for i, v in enumerate(b)] for b in COLLIDERS],  # nothing below the ground
            "particles": [{"type": p["type"], "pos": [round(float(v), 3) for v in p["pos"]], "chance": p.get("chance", 0.3),
                           "count": p.get("count", 1)} for p in particles],
        }
        path = os.path.join(ASSETS, "workshops/%s.json" % name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=1)
        if icon is not None:
            icon(os.path.join(ASSETS, "textures/item/%s.png" % name))
    print("%s: %d cubes, extent %s, %d collision boxes" % (name, len(model["elements"]), ["%.2f" % v for v in ext], len(COLLIDERS)))
    return model


def new_icon(size=32):
    from PIL import Image, ImageDraw
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)


def save_icon(im, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path)
