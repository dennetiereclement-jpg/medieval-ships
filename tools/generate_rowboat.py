#!/usr/bin/env python3
"""Generates the Rowboat (rowboat) Blockbench model, its texture, its item icon and its animations.

Usage:  python3 tools/generate_rowboat.py        (ROWBOAT_OUT=<file>: write the model there only, for previews)

Outputs:
  blockbench/rowboat.bbmodel                                            (editable, texture embedded)
  src/main/resources/assets/medievalships/models/entity/rowboat.bbmodel  (loaded by the mod)
  src/main/resources/assets/medievalships/textures/entity/rowboat.png
  src/main/resources/assets/medievalships/textures/item/rowboat.png

Reference: the rowboat of the sheet "four small vehicles" (docs/ROWBOAT_PLAN.md): a small clinker-built fishing
rowboat of natural brown wood, double-ended, the bow and the stern rising a little; six overlapping strakes a side on
a round section, a thick light gunwale bound with iron bands, pale ribs and dark floorboards inside, three thwarts
just under the gunwale and a small triangular seat board at the stern, square tholepins in pairs, a pair of oars,
a mooring rope turned round the stem post, hanging down the bow and coiled on the bow floor.

The shape follows tools/rowboat_shape.py (the same numbers as RowboatLayout in Java). Bones used by the mod (keep
their names when editing in Blockbench): oar_l1, oar_r1 (animation "row": catch, drive, release, recovery); the
"detail" bone (rope, bands) is hidden far away.
"""
import math
import os
import sys
import uuid

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import generate_galleon as gn  # noqa: E402
import generate_galley as gg  # noqa: E402
import generate_airship as ga  # noqa: E402
import generate_leviathan as gl  # noqa: E402
import rowboat_shape as rs  # noqa: E402
import rowboat_texture as rt  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_uuid_counter = [0]


def new_uuid():
    _uuid_counter[0] += 1
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "medievalships/rowboat/%d" % _uuid_counter[0]))


# the shared helpers write into these (generate_leviathan set them for itself when imported)
gg.new_uuid = new_uuid
gn.new_uuid = new_uuid
gn.REGIONS = {k: (0,) + r for k, r in rt.REGIONS.items()}
gn.SIZE = rt.SIZE

v3, norm, Bone, add_cube, beam = gg.v3, gg.norm, gg.Bone, gg.add_cube, gg.beam
quad, box = gl.quad, gl.box
ring, polyline, catmull = ga.ring, ga.polyline, ga.catmull
EYE = np.eye(3)
SIDES = ((1, "p"), (-1, "s"))

# construction stations (dense towards the pointed ends) and the strakes
# the planking runs on past HALF_LENGTH to close on the posts (hw 0.1 at 2.6; the posts are 0.18 wide)
STATIONS = (-2.6, -2.5, -2.32, -2.05, -1.65, -1.15, -0.6, 0.0, 0.6, 1.15, 1.65, 2.05, 2.32, 2.5, 2.6)
N_STRAKES = 6
PLANK = 0.06        # thickness of the planking
LAP = 0.025         # each strake stands this much outside the one below (clinker)
RIB_TH = 0.1        # ribs: thickness (in from the planking) and width (along the hull)
RIB_W = 0.08


# ================================================================ sections
def section_curve(z):
    """Dense half section (x, y) on the port side, keel to rail, outside of the planking."""
    hw, yk, yr = rs.half_width(z), rs.keel_y(z), rs.rail_y(z)
    ctrl = [v3(max(0.1, fx * hw), fy * yk, z) for fx, fy in rs.BOTTOM_SECTION]
    y0 = ctrl[-1][1]
    ctrl += [v3(1.005 * hw, y0 + (yr - y0) * 0.5, z), v3(1.02 * hw, yr, z)]
    pts = catmull(ctrl, 6)
    return [p for i, p in enumerate(pts) if i == 0 or np.linalg.norm(p - pts[i - 1]) > 1e-6]


def resample(pts, n):
    """n + 1 points along the polyline at equal arc length."""
    seg = [np.linalg.norm(pts[i + 1] - pts[i]) for i in range(len(pts) - 1)]
    total = sum(seg)
    out = [pts[0]]
    for k in range(1, n):
        target = total * k / n
        acc = 0.0
        for i, L in enumerate(seg):
            if acc + L >= target:
                t = (target - acc) / L if L > 1e-9 else 0.0
                out.append(pts[i] + (pts[i + 1] - pts[i]) * t)
                break
            acc += L
    out.append(pts[-1])
    return out


def section(z, side):
    """The N_STRAKES + 1 strake edges of one side (keel first), and the outward normal at each."""
    pts = resample(section_curve(z), N_STRAKES)
    normals = []
    for i, p in enumerate(pts):
        a = pts[max(0, i - 1)]
        b = pts[min(len(pts) - 1, i + 1)]
        t = b - a
        n = norm(v3(t[1], -t[0], 0))   # perpendicular in the section plane, pointing out and down
        if n[0] < 0:
            n = -n
        normals.append(n)
    return [v3(side * p[0], p[1], p[2]) for p in pts], [v3(side * n[0], n[1], n[2]) for n in normals]


def side_x(z, y):
    """Half width of the outside of the planking at height y on the topsides (above the turn of the bilge)."""
    hw, yk, yr = rs.half_width(z), rs.keel_y(z), rs.rail_y(z)
    y0 = rs.BOTTOM_SECTION[-1][1] * yk
    t = max(0.0, min(1.0, (y - y0) / (yr - y0)))
    return hw * (0.97 + 0.05 * t)


def inner_x(z, y):
    """Inside of the ribs at height y (where the thwarts, risers and seats rest)."""
    return side_x(z, y) - PLANK - RIB_TH


# ================================================================ hull
def hull(bone, detail):
    # the clinker strakes, each standing LAP outside the one below
    for side, sn in SIDES:
        secs = [section(z, side) for z in STATIONS]
        for k in range(N_STRAKES):
            region = "strake_low" if k < 2 else "strake_up" if k == N_STRAKES - 1 else "strake"
            for i in range(len(STATIONS) - 1):
                (A, An), (B, Bn) = secs[i], secs[i + 1]
                off = LAP * k
                a0, a1 = A[k] + An[k] * off, A[k + 1] + An[k + 1] * off
                b0, b1 = B[k] + Bn[k] * off, B[k + 1] + Bn[k + 1] * off
                L = np.linalg.norm((b0 + b1) / 2 - (a0 + a1) / 2)
                u0 = ((i * 13 + k * 7) % 52) / 64.0
                u1 = min(1.0, u0 + L * 16 / 64.0)
                outward = norm(v3(side, -0.9 if k < 2 else -0.25 if k < 3 else 0.1, 0.0))
                quad(bone, "strake_%s%d_%d" % (sn, k, i), a0, b0, a1, b1, PLANK, region, outward, sub=(u0, 0.0, u1, 1.0),
                     u_dir=v3(0, 0, 1), v_dir=v3(0, -1, 0), back="inner", overlap=(1.04, 1.12))
    # the keel plank under the garboards, sweeping up into the posts
    kz = (-2.6, -2.1, -1.5, -0.75, 0.0, 0.75, 1.5, 2.1, 2.6)
    for i in range(len(kz) - 1):
        p0, p1 = v3(0, rs.keel_y(kz[i]) - 0.025, kz[i]), v3(0, rs.keel_y(kz[i + 1]) - 0.025, kz[i + 1])
        beam(bone, "keel_%d" % i, p0, p1, 0.07, "keel", width=0.3, extend=0.02)
    # the stem and stern posts: square timbers, slightly raked, standing above the rail
    for side, name in ((1, "stem_post"), (-1, "stern_post")):
        zs = side * (rs.HALF_LENGTH + 0.1)
        foot = v3(0, rs.keel_y(rs.HALF_LENGTH) - 0.04, zs)
        top = v3(0, rs.rail_y(rs.HALF_LENGTH) + rs.GUNWALE_H + rs.POST_TOP, side * (rs.TIP - rs.POST_W / 2))
        beam(bone, name, foot, top, rs.POST_W, {"all": "post", "+1": "end_grain", "-1": "end_grain"}, width=rs.POST_W, extend=0.0)
    # ribs: a floor timber across the bottom, two futtocks up each side, inside the planking
    for j, z in enumerate(rs.RIB_Z):
        P, Pn = section(z, 1)
        S, Sn = section(z, -1)
        inset = PLANK + RIB_TH / 2
        pin = [P[k] - Pn[k] * inset for k in range(len(P))]
        sin_ = [S[k] - Sn[k] * inset for k in range(len(S))]
        kb, kw, kr = 2, 4, N_STRAKES
        floor_y = min(pin[kb][1], rs.keel_y(z) + PLANK + RIB_TH / 2 + 0.01)
        a, b = v3(sin_[kb][0], floor_y, z), v3(pin[kb][0], floor_y, z)
        beam(bone, "rib_floor_%d" % j, a, b, RIB_TH, "rib", width=RIB_W, up=v3(0, 1, 0), extend=0.03)
        for side, sn, pts in ((1, "p", pin), (-1, "s", sin_)):
            up = v3(side, 0, 0)
            beam(bone, "rib_%s%d_a" % (sn, j), v3(pts[kb][0], floor_y, z), pts[kw], RIB_TH, "rib", width=RIB_W, up=up, extend=0.03)
            beam(bone, "rib_%s%d_b" % (sn, j), pts[kw], pts[kr] + v3(0, -0.02, 0), RIB_TH, "rib", width=RIB_W, up=up, extend=0.02)
    # floorboards: three dark boards along the bottom, on the floor timbers, following the rocker
    fz = (-1.95, -0.65, 0.65, 1.95)
    for bx, x in enumerate((-0.3, 0.0, 0.3)):
        for i in range(len(fz) - 1):
            p0 = v3(x, rs.keel_y(fz[i]) + PLANK + RIB_TH + 0.02, fz[i])
            p1 = v3(x, rs.keel_y(fz[i + 1]) + PLANK + RIB_TH + 0.02, fz[i + 1])
            beam(bone, "floor_%d_%d" % (bx, i), p0, p1, 0.04, "floor", width=0.26, extend=0.01)


# ================================================================ fittings
def gunwale(bone, detail):
    yr = rs.rail_y
    for side, sn in SIDES:
        # the thick light rail, covering the sheer strake and the ribs' heads
        for i in range(len(STATIONS) - 1):
            za, zb = STATIONS[i], STATIONS[i + 1]
            pa = v3(side * (side_x(za, yr(za)) + 0.1 - rs.GUNWALE_W / 2 + 0.02), yr(za) + rs.GUNWALE_H / 2 - 0.02, za)
            pb = v3(side * (side_x(zb, yr(zb)) + 0.1 - rs.GUNWALE_W / 2 + 0.02), yr(zb) + rs.GUNWALE_H / 2 - 0.02, zb)
            beam(bone, "gunwale_%s%d" % (sn, i), pa, pb, rs.GUNWALE_H, "gunwale", width=rs.GUNWALE_W, extend=0.03)
        # the riser: a stringer along the inside of the ribs, carrying the thwarts
        for i in range(2, len(STATIONS) - 3):
            za, zb = STATIONS[i], STATIONS[i + 1]
            y = rs.THWART_TOP - rs.THWART_TH - 0.04
            pa = v3(side * (inner_x(za, y) - 0.03), y, za)
            pb = v3(side * (inner_x(zb, y) - 0.03), y, zb)
            beam(bone, "riser_%s%d" % (sn, i), pa, pb, 0.08, "gunwale", width=0.06, extend=0.03)
        # iron bands round the rail, a riveted strap down the sheer strake under each
        for k, z in enumerate(rs.BAND_Z):
            xc = side * (side_x(z, yr(z)) + 0.1 - rs.GUNWALE_W / 2 + 0.02)
            box(detail, "band_%s%d" % (sn, k), (xc, yr(z) + rs.GUNWALE_H / 2 - 0.02, z), (rs.GUNWALE_W + 0.03, rs.GUNWALE_H + 0.03, 0.05), "iron")
            xo = side * (side_x(z, yr(z) - 0.17) + 5 * LAP + 0.012)
            box(detail, "strap_%s%d" % (sn, k), (xo, yr(z) - 0.17, z), (0.025, 0.24, 0.05), "iron")
        # the tholepins: two pairs a side (the rower's, and a forward position)
        for name, zl in (("lock", rs.OARLOCK_Z), ("fore", rs.FORE_LOCK_Z)):
            for q, dz in enumerate((-rs.PIN_GAP, rs.PIN_GAP)):
                z = zl + dz
                xc = side * (side_x(z, yr(z)) + 0.1 - rs.GUNWALE_W / 2 + 0.02)
                y0 = yr(z) + rs.GUNWALE_H - 0.06
                beam(bone, "pin_%s_%s%d" % (name, sn, q), v3(xc, y0, z), v3(xc, y0 + 0.32, z), 0.08,
                     {"all": "post", "+1": "end_grain", "-1": "end_grain"}, width=0.08)


def seats(bone):
    y = rs.THWART_TOP - rs.THWART_TH / 2
    for j, z in enumerate(rs.THWART_Z):
        hw = inner_x(z, rs.THWART_TOP) + 0.05
        beam(bone, "thwart_%d" % j, v3(-hw, y, z), v3(hw, y, z), rs.THWART_TH, "thwart", width=rs.THWART_W, up=v3(0, 1, 0), extend=0.0,
             u_dir=v3(1, 0, 0))
        # a knee under each end of the thwart, against the ribs (the brackets of the reference)
        for side, sn in SIDES:
            xk = side * (inner_x(z, rs.THWART_TOP - 0.2) - 0.09)
            box(bone, "knee_%d_%s" % (j, sn), (xk, rs.THWART_TOP - rs.THWART_TH - 0.12, z), (0.16, 0.24, 0.1), "rib")
    # the small triangular seat board at the stern: two boards narrowing towards the stern post
    z0, z1 = rs.STERN_SEAT_Z
    for j, (za, zb) in enumerate(((z1, z1 - 0.3), (z1 - 0.3, z0))):
        zc = (za + zb) / 2
        hw = inner_x(zc, rs.THWART_TOP) + 0.06
        beam(bone, "stern_seat_%d" % j, v3(-hw, y, zc), v3(hw, y, zc), rs.THWART_TH, "seat", width=abs(za - zb), up=v3(0, 1, 0))


def oars(root):
    for side, sn in SIDES:
        group = Bone("oars_" + ("left" if side > 0 else "right"), parent=root)
        pivot = v3(*rs.oar_pivot(side))
        d = v3(*rs.oar_dir(side))
        ob = Bone("oar_%s1" % ("l" if side > 0 else "r"), origin=pivot, parent=group)
        gg._rbeam(ob, "oar_shaft_%s" % sn, pivot - d * (rs.OAR_IN - 0.25), pivot + d * (rs.OAR_OUT - rs.OAR_BLADE + 0.05), rs.OAR_TH, "oar")
        beam(ob, "oar_grip_%s" % sn, pivot - d * rs.OAR_IN, pivot - d * (rs.OAR_IN - 0.28), rs.OAR_TH + 0.03, "keel", width=rs.OAR_TH + 0.03)
        beam(ob, "oar_blade_%s" % sn, pivot + d * (rs.OAR_OUT - rs.OAR_BLADE), pivot + d * rs.OAR_OUT, rs.OAR_BLADE_W, "blade", width=0.045,
             up=v3(0, 1, 0))
        # the leather collar where the oar rests between the pins
        beam(ob, "oar_collar_%s" % sn, pivot - d * 0.09, pivot + d * 0.09, rs.OAR_TH + 0.05, "keel", width=rs.OAR_TH + 0.05)


def mooring_rope(bone):
    zs = rs.TIP - rs.POST_W / 2
    top = rs.rail_y(rs.HALF_LENGTH) + rs.GUNWALE_H + rs.POST_TOP
    # two turns round the stem post
    for k, dy in enumerate((0.1, 0.19)):
        ring(bone, "rope_turn_%d" % k, v3(0, top - 0.3 + dy, zs - 0.02), v3(0, 1, 0), rs.POST_W / 2 + 0.055, 0.085, "rope", n=6,
             phase=0.3 * k)
    # the bight hanging down the port side of the bow, its end dipping towards the water
    yb = top - 0.22
    pts = [v3(0.14, yb, zs + 0.02), v3(0.3, yb - 0.3, zs - 0.02), v3(0.44, yb - 0.65, zs - 0.18), v3(0.52, yb - 0.95, zs - 0.42),
           v3(0.5, yb - 1.1, zs - 0.62)]
    polyline(bone, "rope_bight", catmull(pts, 2), 0.085, "rope", sides=4)
    # the coil on the bow floor and the rope leading up to the post
    zc = 1.9
    yf = rs.keel_y(zc) + PLANK + RIB_TH + 0.04
    ring(bone, "rope_coil_0", v3(0.0, yf + 0.045, zc), v3(0, 1, 0), 0.32, 0.085, "rope", n=8)
    ring(bone, "rope_coil_1", v3(0.03, yf + 0.125, zc + 0.02), v3(0, 1, 0), 0.25, 0.085, "rope", n=8, phase=0.2)
    ring(bone, "rope_coil_2", v3(-0.02, yf + 0.2, zc - 0.02), v3(0, 1, 0), 0.19, 0.08, "rope", n=6, phase=0.5)
    polyline(bone, "rope_lead", [v3(0.1, yf + 0.22, zc + 0.2), v3(0.1, yb - 0.45, zs - 0.28), v3(0.08, yb - 0.02, zs - 0.12)], 0.085, "rope",
             sides=4)
    # a second line over the port gunwale abaft the rower, hanging down the side to the water (the reference's rope)
    zr = -0.45
    xo = side_x(zr, rs.rail_y(zr)) + 5 * LAP + 0.06
    pts = [v3(inner_x(zr, 0.3) - 0.15, rs.THWART_TOP - 0.25, zr + 0.3), v3(xo - 0.2, rs.rail_y(zr) + rs.GUNWALE_H + 0.06, zr + 0.05),
           v3(xo + 0.02, rs.rail_y(zr) - 0.1, zr - 0.1), v3(xo + 0.06, 0.25, zr - 0.3), v3(xo + 0.3, 0.02, zr - 0.5)]
    polyline(bone, "rope_side", catmull(pts, 2), 0.085, "rope", sides=4)


# ================================================================ model
def build():
    root = Bone("rowboat")
    hull_b = Bone("hull", parent=root)
    fittings = Bone("fittings", parent=root)
    detail = Bone("detail", parent=root)
    hull(hull_b, detail)
    gunwale(fittings, detail)
    seats(fittings)
    oars(root)
    mooring_rope(detail)
    return root


def build_animations(root):
    # the rowing cycle (2 s): catch with the blade forward and in the water, drive aft, release (lift), recovery forward
    cycle = [(0.0, 22, -8), (0.9, -22, -8), (1.1, -24, 12), (1.8, 20, 12), (2.0, 22, -8)]
    tracks = []
    for side, name in ((1, "oar_l1"), (-1, "oar_r1")):
        b = gg.find(root, name)
        kfs = [gg.rot_kf(t, (0,) + tuple(gg.oar_euler(side, sweep, lift))) for t, sweep, lift in cycle]
        tracks.append((b, kfs))
    return [gg.animation("row", 2.0, "loop", tracks)]


def main():
    root = build()
    gg.verify_oar_signs(root)
    anims = build_animations(root)
    tex_dir = os.path.join(ROOT, "src/main/resources/assets/medievalships/textures")
    tex_path = os.path.join(tex_dir, "entity/rowboat.png")
    rt.make_texture(tex_path)
    rt.make_item_icon(os.path.join(tex_dir, "item/rowboat.png"))
    with open(tex_path, "rb") as f:
        png = f.read()
    textures = [gn.texture_entry("rowboat.png", rt.SIZE, png, "entity", "rowboat.png")]
    textures[0]["id"] = "0"
    out = [os.path.join(ROOT, "blockbench/rowboat.bbmodel"),
           os.path.join(ROOT, "src/main/resources/assets/medievalships/models/entity/rowboat.bbmodel")]
    if os.environ.get("ROWBOAT_OUT"):
        out = [os.environ["ROWBOAT_OUT"]]
    model = gn.export(root, anims, textures, out, name="rowboat", visible_box=(6, 3, 0))
    n_groups = [0]

    def count(g):
        n_groups[0] += 1
        for c in g["children"]:
            if isinstance(c, dict):
                count(c)
    count(model["outliner"][0])
    print("cubes:", len(model["elements"]), "bones:", n_groups[0], "animations:", [a["name"] for a in model["animations"]])


if __name__ == "__main__":
    main()
