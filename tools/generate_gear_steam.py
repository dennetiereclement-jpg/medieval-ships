#!/usr/bin/env python3
"""Generates the Gear Steamship (gear_steamship) Blockbench model, its textures, its item icon, its interior
grid and its furniture.

Usage:  python3 tools/generate_gear_steam.py

Outputs:
  blockbench/gear_steamship.bbmodel                                             (editable, textures embedded)
  src/main/resources/assets/medievalships/models/entity/gear_steamship.bbmodel  (loaded by the mod)
  src/main/resources/assets/medievalships/textures/entity/gear_steamship.png
  src/main/resources/assets/medievalships/textures/entity/gear_steamship_sails.png
  src/main/resources/assets/medievalships/textures/item/gear_steamship.png
  src/main/resources/assets/medievalships/interiors/gear_steamship.grid         (collisions, dry rooms, doors, ladders)
  src/main/resources/assets/medievalships/interiors/gear_steamship_decor.json   (furniture of the mods, seats)

Reference: the picture of the "Navire a vapeur a engrenages" (docs/GearSteam_PLAN.md, one starboard view at
sunset): a long iron-plated hull of black riveted plates with stepped copper and brass trims and a copper
boot-top, copper pipes along the side, two big brass gear wheels on the side (a big one amidships, a smaller
one at the bow), square windows glowing orange; a raised poop with a crane at the stern (a crate hanging on
two chains) and a stern gallery; the captain's deckhouse (three lit windows a side) with the bridge on its
roof; the engine house flush with the sides carrying a riveted copper dome banded with brass and a tall
black riveted funnel with a brass band; a low waist with copper railings; a raised forecastle with a tall
prow trimmed with brass and a boom carrying a lantern; two masts with black square sails bordered with
gold (a big gold gear on the main sail), chain rigging, lanterns. Inside: the engine room with its boiler,
the crew quarters, the captain's cabin, the hold; their walls, floors and ceilings are drawn on the
boundaries of the interior grid (tools/gear_steam_interior.py): what is drawn is what collides.

Bones used by the mod (keep their names when editing in Blockbench):
  sail_* (sail_wind, sail_furl)  helm_wheel, rudder (steer)  gear_* (engine: the gear wheels turn with the speed;
  gear_flywheel: the engine room's flywheel)  piston_* (engine: the engine room's pistons)
  lantern_*, crate_hang (lantern_sway)   door_<k> (door k: 0 = closed, 1 = open)   rooms, furniture, fittings, detail
"""
import math
import os
import sys
import uuid

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import generate_galleon as gn  # noqa: E402
import generate_galley as gg  # noqa: E402
import generate_corsair as gc  # noqa: E402   (generic helpers only: lanterns, sail patches, ladders, furniture, greedy)
import corsair_furniture as cf  # noqa: E402,F401
import gear_steam_shape as gs  # noqa: E402
import gear_steam_interior as gi  # noqa: E402
import gear_steam_texture as gt  # noqa: E402
import gear_steam_decor as gd  # noqa: E402
import gear_steam_furniture as gf  # noqa: E402   (imports generate_airship: its module settings are overridden below)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_uuid_counter = [0]


def new_uuid():
    _uuid_counter[0] += 1
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "medievalships/gear_steamship/%d" % _uuid_counter[0]))


gg.new_uuid = new_uuid
gn.new_uuid = new_uuid
gc.new_uuid = new_uuid
REGIONS = {k: (0,) + r for k, r in gt.REGIONS.items()}
REGIONS.update({k: (1,) + r for k, r in gt.SAIL_REGIONS.items()})   # the sails: second texture
gn.REGIONS = REGIONS
gn.SIZE = gt.SIZE
_face_uv_16 = gn.face_uv


def _face_uv_hd(cube, bbface, spec, seed):
    """The atlases are painted at 32 px a block (1.27.1, gear_steam_texture.K): a face that samples its region at its
    own size (not stretched, no sub-rectangle) takes K times as many texels, so that a block stays a block."""
    if spec.get("sub") is None and not spec["stretch"]:
        spec = dict(spec, density=spec["density"] * gt.K)
    return _face_uv_16(cube, bbface, spec, seed)


gn.face_uv = _face_uv_hd

v3, norm, Bone, add_cube, beam, board = gg.v3, gg.norm, gg.Bone, gg.add_cube, gg.beam, gg.board
ry = gg.ry
round_bar, disc, turned, polyline = gn.round_bar, gn.disc, gn.turned, gn.polyline
lantern, patch_sail = gc.lantern, gc.patch_sail
EYE = np.eye(3)
SIDES = ((1, "p"), (-1, "s"))
DECK_AXES = np.column_stack([v3(0, 0, 1), v3(0, 1, 0), v3(-1, 0, 0)])

M, H, P, F, E, B = gs.MAIN_DECK_Y, gs.HOLD_FLOOR_Y, gs.POOP_Y, gs.FORECASTLE_Y, gs.ENGINE_ROOF_Y, gs.BRIDGE_Y
TZ = gs.TRANSOM_Z
PF, EF, FZ = gs.POOP_FRONT_Z, gs.ENGINE_FRONT_Z, gs.FORECASTLE_Z
DZ0, DZ1 = gs.DECKHOUSE_Z
DH = gs.DECKHOUSE_HALF
BOW_Z = gs.FORE_SCALE - 0.02
BRACE = math.radians(gs.BRACE_DEG)


# ---------------------------------------------------------------- hull geometry
def hp(z, y, side, out=0.0):
    """Point on the outer hull surface (or above its top, on the wall line), pushed out by `out`."""
    return v3(side * (gs.hull_x(z, y) + out), y, z)


def side_frame(z, y, side):
    """Point on the hull side, u along +z (on the surface), v up the surface, n outward."""
    d = 0.05
    p = hp(z, y, side)
    u = norm(hp(z + d, y, side) - hp(z - d, y, side))
    vv = hp(z, y + d, side) - hp(z, y - d, side)
    v = norm(vv - np.dot(vv, u) * u)
    n = np.cross(u, v)
    if np.dot(n, v3(side, 0, 0)) < 0:
        u, n = -u, -n
    return p, u, v, n


def hull_decal(bone, name, z, y, side, w, h, region, out=0.012, th=0.03, glow=False, stretch=True):
    p, u, v, n = side_frame(z, y, side)
    c = p + n * (out + th / 2)
    return add_cube(bone, ("glow_" if glow else "") + name, c, np.column_stack([u, v, n]), (w, h, th), region, stretch=stretch,
                    u_dir=-u if side > 0 else u, v_dir=v3(0, -1, 0))


def stem_clip(z, y):
    return min(z, BOW_Z + gs.rake(BOW_Z, y))


def cap_region(z):
    if PF <= z < EF:
        return "stone"
    return "copper2"


def hull_rows(z):
    """Points (x, y) of the outer hull section at z (one side, keel to the top) and the region of each strip:
    dark plates under the water, the copper boot-top, iron plates, the riveted cap (copper; dark stone on the
    engine house)."""
    top = gs.top_y(z)
    pts = []
    for fx, fy in ((0.0, 1.0), (0.5, 0.92), (0.82, 0.6), (0.97, 0.15)):
        y = fy * gs.keel_draw(min(z, gs.HALF_LENGTH + 0.6))
        zz = z - gs.rake(z, y)
        w, yk = gs.half_width(zz), gs.keel_draw(min(zz, gs.HALF_LENGTH + 0.6))
        pts.append((max(0.16, fx * w), fy * yk if yk < 0 else yk + 0.15 * (1 - fy)))
    regs = ["plate_c", "plate_c", "plate_c"]
    cap = 0.5 if z < FZ or z > 19.0 else 0.6     # the forecastle: one broad copper course, as on the reference
    r = gs.STEP_ROWS     # the copper boot-top shows above the water (as on the reference), then the stepped rows of plates
    levels = [(gs.STEP_LOW, "plate_c"), (r[0], "copper"), (r[1], "plate_a"), (r[2], "plate_a"), (r[3], "plate_a"),
              (3.35 + (top - cap - 3.35) * 0.5, "plate_a"), (top - cap, "plate_a"), (top, cap_region(z))]
    for y, reg in levels:
        y = max(y, pts[-1][1] + 0.08)
        if any(abs(pts[-1][1] - t) < 1e-6 for t in gs.STEP_ROWS[:-1]) and gs.rake(z, y) != gs.rake(z, pts[-1][1]):
            # the bow's stepped rows (phase 4): a ledge from the top of a row to the foot of the one above it, so that
            # each row stands upright with its own fore end
            yl = pts[-1][1] + 0.003
            pts.append((max(0.16, gs.hull_x(z, yl)), yl))
            regs.append(reg)
        pts.append((max(0.16, gs.hull_x(z, y)), y))
        regs.append(reg)
    return pts, regs


PLATES = ("plate_a", "plate_b", "plate_c")
BANDS = ("copper", "copper2", "stone", "brass_band", "iron_band")


def map_strip(cube, region, z0, y_lo):
    """The plates and bands run on from board to board: each board shows the stretch of its region (4 blocks
    long for the bands, 8 for the plates) that its position along the hull falls on; plates also follow their height
    (4 blocks of plates)."""
    rw, rh = gt.LAYOUT[region][2:]
    lu = min(1.0, cube.size[0] * 16 / rw)
    u0 = ((z0 - TZ) * 16 % rw) / rw
    if u0 + lu > 1:
        u0 = max(0.0, 1 - lu)
    if region in PLATES:
        lv = min(1.0, cube.size[1] * 16 / rh)
        v0 = ((y_lo + 0.3) * 16 % rh) / rh
        if v0 + lv > 1:
            v0 = max(0.0, 1 - lv)
        sub = (u0, v0, u0 + lu, v0 + lv)
    else:
        sub = (u0, 0.0, u0 + lu, 1.0)
    for spec in cube.faces.values():
        if spec is not None and spec["region"] == region:
            spec["sub"] = sub
            spec["u_dir"], spec["v_dir"] = v3(0, 0, 1), v3(0, -1, 0)


def _stations():
    st = [TZ, -15.6, -15.0, -14.3, -13.5, -12.0, -10.5, -9.0, -7.5]
    st += [PF - 0.001, PF + 0.001, -5.0, -3.5, -2.0, -0.5, 1.0, 2.5, 4.0, EF - 0.001, EF + 0.001, 6.5, 8.0, 9.5, 11.0, FZ - 0.001, FZ + 0.001]
    st += [12.5, 13.5, 14.5, 15.4, 16.2, 17.0, 17.7, 18.2, 18.6, BOW_Z, 19.2, 19.7, 20.2, 20.7, 21.2, 21.7]
    # the stepped counter (phase 4): a pair of stations round each step, the boards on either side of it take its two heights
    for z, _, _ in gs.counter_steps(TZ):
        st += [z - 0.002, z + 0.002]
    st += [gs.stem_z(t) - 0.001 for t in gs.STEP_ROWS[:-1]] + [gs.stem_z(t) + 0.001 for t in gs.STEP_ROWS[:-1]]
    return sorted(set(round(z, 4) for z in st if TZ <= z))


STATIONS = _stations()


def hull(bone):
    n = 0
    for side, sn in SIDES:
        for i in range(len(STATIONS) - 1):
            za, zb = STATIONS[i], STATIONS[i + 1]
            if zb - za < 0.01:
                continue
            zm = (za + zb) / 2
            # at a step of the hull's top (the pair of stations around it) each board takes the top of its own side
            A, regs = hull_rows(za if gs.top_y(za) == gs.top_y(zm) else za + 0.002)
            B, _ = hull_rows(zb if gs.top_y(zb) == gs.top_y(zm) else zb - 0.002)
            for k in range(len(A) - 1):
                a0, a1 = v3(side * A[k][0], A[k][1], stem_clip(za, A[k][1])), v3(side * A[k + 1][0], A[k + 1][1], stem_clip(za, A[k + 1][1]))
                b0, b1 = v3(side * B[k][0], B[k][1], stem_clip(zb, B[k][1])), v3(side * B[k + 1][0], B[k + 1][1], stem_clip(zb, B[k + 1][1]))
                if np.linalg.norm((b0 + b1) - (a0 + a1)) < 0.02 or np.linalg.norm((a1 + b1) - (a0 + b0)) < 0.02:
                    continue
                mid = (a0 + a1 + b0 + b1) / 4
                t = (a1 + b1) - (a0 + b0)
                outward = norm(v3(side * t[1], -side * t[0], 0) + v3(0, 0, 0.6 * max(0.0, mid[2] - 13) / 6))
                cube = board(bone, "hull_%s%d_%d" % (sn, i, k), a0, a1, b0, b1, 0.14, regs[k], outward, overlap=1.03,
                             inner="plate_c" if k < 5 else "plate_b")
                map_strip(cube, regs[k], za, min(a0[1], b0[1]))
                n += 1
    # the risers of the stepped counter (the aft faces of its rows)
    for j, (z, lo, hi) in enumerate(gs.counter_steps(TZ)):
        w = 0.97 * gs.half_width(z)
        add_cube(bone, "counter_riser_%d" % j, (0, (lo + hi) / 2, z), EYE, (2 * w, hi - lo + 0.02, 0.1), "plate_c")
    # keel, rising into the stem
    for i in range(len(STATIONS) - 2):
        za, zb = STATIONS[i], STATIONS[i + 1]
        if zb > gs.HALF_LENGTH + 0.2 or zb - za < 0.01:
            continue
        beam(bone, "keel_%d" % i, (0, gs.keel_draw(za) - 0.08, za), (0, gs.keel_draw(zb) - 0.08, zb), 0.3, "iron_dark", width=0.36, extend=0.06)
    return n


def stem(bone):
    """The brass stem: a broad brass strip along the raked stem from under the water up to the stem head (stepped
    as on the reference), the raised prow behind it above the forecastle (stepped black plated walls rising to
    the head on both sides, a brass-capped head) and the boom carrying the great lantern."""
    yt = gs.STEM_HEAD[1]
    ys = sorted(set([round(y, 3) for y in np.arange(-1.6, yt - 0.2, 0.5)] + [yt] + [t for t in gs.STEP_ROWS]))
    for k in range(len(ys) - 1):
        ya, yb = ys[k], ys[k + 1]
        if ya < gs.STEP_ROWS[-1] - 1e-6 and yb > gs.STEP_ROWS[0] - 0.66:
            # the stepped rows: a brass block upright on each row (its fore end), stepping back row by row
            zm = gs.stem_z((ya + yb) / 2) + 0.05
            add_cube(bone, "stem_%d" % k, (0, (ya + yb) / 2, zm - 0.15), EYE, (0.7, yb - ya + 0.02, 0.55), "brass_band")
            continue
        za, zb = gs.stem_z(ya) + 0.05, gs.stem_z(yb) + 0.05
        add_cube(bone, "stem_%d" % k, (0, (ya + yb) / 2, (za + zb) / 2 - 0.15), EYE, (0.7, yb - ya + 0.02, abs(zb - za) + 0.5), "brass_band")
    # brass cheeks wrapping the stem on both sides, from the water up to the head (the broad brass stem of the
    # reference, two blocks wide seen from the side, stepping with the rake)
    for side, sn in SIDES:
        for k, y in enumerate(np.arange(-0.25, gs.FORECASTLE_CAP_Y + 0.01, 0.5)):
            hull_decal(bone, "stem_cheek_%s%d" % (sn, k), gs.stem_z(y) - 0.62, y, side, 1.15, 0.52, "brass_band", out=0.02, th=0.06,
                       stretch=False)
    # the raised prow, as on the reference: a raked neck (black plates, brass-faced) rising from the forecastle cap to
    # the head, and a stepped brace (one block thick, open under it) running down aft from the head to the
    # forecastle railing
    yc = gs.FORECASTLE_CAP_Y
    zh = gs.stem_z(yt)
    nys = list(np.arange(yc - 0.5, yt - 0.2, 0.5)) + [yt]
    for k in range(len(nys) - 1):
        ya, yb = nys[k], nys[k + 1]
        zf = gs.stem_z((ya + yb) / 2) - 0.1
        add_cube(bone, "prow_neck_%d" % k, (0, (ya + yb) / 2, zf - 1.25), EYE, (1.0, yb - ya + 0.02, 2.3), "plate_a", stretch=True)
        for side, sn in SIDES:
            add_cube(bone, "prow_cheek_%s%d" % (sn, k), (side * 0.53, (ya + yb) / 2, zf - 0.5), EYE, (0.06, yb - ya + 0.02, 1.1), "brass_band")
    add_cube(bone, "prow_head", (0, yt - 0.25, zh - 1.3), EYE, (1.0, 0.5, 2.4), "plate_a")
    add_cube(bone, "prow_cap", (0, yt + 0.12, zh - 0.45), EYE, (1.0, 0.24, 1.4), "brass_band")
    za, ya = zh - 2.45, yt - 0.25          # the brace: from under the head down to the railing, steps of half a block
    zb, yb = 15.6, gs.FORECASTLE_BULWARK_TOP + 0.95
    n = int(round((ya - yb) / 0.5))
    for k in range(n + 1):
        y = ya - k * 0.5
        z0 = za - k * (za - zb) / n
        add_cube(bone, "prow_brace_%d" % k, (0, y, z0 - 0.35), EYE, (0.5, 0.5, (za - zb) / n + 0.3), "plate_a" if k % 2 else "plate_b")
        add_cube(bone, "prow_brace_cap_%d" % k, (0, y + 0.27, z0 - 0.35), EYE, (0.54, 0.06, (za - zb) / n + 0.32), "iron_band")
    # the boom: a copper-banded spar forward from the stem head, a bracket under it, brass bands
    bt = v3(*gs.BOOM_TIP)
    root = v3(0, yt - 0.25, zh - 0.6)
    beam(bone, "boom", root, bt, 0.5, "copper2", width=0.5, extend=0.1)
    beam(bone, "boom_bracket", v3(0, yt - 1.9, gs.stem_z(yt - 1.9) + 0.05), root + v3(0, -0.05, 1.5), 0.3, "brass", width=0.3)
    for k, t in enumerate((0.35, 0.7, 0.98)):
        p = root + (bt - root) * t
        add_cube(bone, "boom_band_%d" % k, p, EYE, (0.58, 0.58, 0.14), "brass")
    return bt


def stern(bone, lights):
    """The flat transom (iron plates over the counter) and, under the poop's overhang, the stern gallery: a
    balcony off the crew quarters on brass knees (floor, plated bulwark with a copper cap and a railing up to
    the overhang, a gear wheel and a lantern on each side), the poop deck carried aft over it on corner posts,
    its plated fascia, copper cap and railing (the taffrail)."""
    z = TZ
    pts, regs = hull_rows(z)
    rows = [(p, r) for p, r in zip(pts, regs) if p[1] < P - 0.45]
    pts = [p for p, _ in rows] + [(gs.hull_x(z, P - 0.5), P - 0.5)]
    regs = [r for _, r in rows]
    for k in range(len(pts) - 1):
        (xa, ya), (xb, yb) = pts[k], pts[k + 1]
        for j in range(4):
            fa0, fa1 = -1 + j / 2, -1 + (j + 1) / 2
            cube = board(bone, "transom_%d_%d" % (k, j), v3(fa0 * xa, ya, z), v3(fa0 * xb, yb, z), v3(fa1 * xa, ya, z), v3(fa1 * xb, yb, z),
                         0.16, regs[k], v3(0, 0, -1), overlap=1.02, inner="plate_b")
            map_strip(cube, regs[k], fa0 * 4, ya)
    add_cube(bone, "transom_band", (0, 3.9, z - 0.1), EYE, (2 * gs.hull_x(z, 3.9) - 0.1, 0.4, 0.06), "copper")
    gx0, gx1, gy0, gy1, gz0, gz1 = gi.GALLERY
    oz = gs.OVERHANG_Z
    zc = (gz0 + gz1) / 2
    xw = gx1 + 0.25
    add_cube(bone, "gallery_floor", (0, M - 0.25, zc - 0.25), EYE, (gx1 - gx0 + 1.0, 0.5, gz1 - gz0 + 0.5), {"all": "plate_b", "+2": "deck"})
    add_cube(bone, "gallery_under", (0, M - 0.7, zc), EYE, (gx1 - gx0 + 0.6, 0.4, gz1 - gz0 - 0.2), "plate_c")
    # under the gallery, the stepped counter runs on aft in rows of plates up to the gallery's floor (the stern of the
    # reference, a staircase of blocks from the water to the gallery), with a copper course on its rows
    yu = M - 0.9
    for j, (za_, zb_, yb) in enumerate(gs.skirt_rows(gz0)):
        if yb >= yu - 0.05:
            continue
        cube = add_cube(bone, "counter_skirt_%d" % j, (0, (yb + yu) / 2 + 0.02, (za_ + zb_) / 2), EYE, (gx1 - gx0 + 0.5, yu - yb + 0.04, zb_ - za_ + 0.01),
                        {"all": "plate_c", "-2": "plate_c"})
        map_strip(cube, "plate_c", za_, yb)
        add_cube(bone, "counter_skirt_band_%d" % j, (0, yb + 0.06, (za_ + zb_) / 2 - 0.01), EYE, (gx1 - gx0 + 0.56, 0.12, zb_ - za_ + 0.04), "copper2")
    for side, sn in SIDES:
        x = side * xw
        add_cube(bone, "gallery_wall_" + sn, (x, (M + gy1) / 2, zc - 0.25), EYE, (0.5, gy1 - M, gz1 - gz0 + 0.5), "plate_b")
        add_cube(bone, "gallery_cap_" + sn, (x, gy1 + 0.06, zc - 0.25), EYE, (0.6, 0.12, gz1 - gz0 + 0.6), "copper2")
        gear(bone, "gear_gallery_" + sn, v3(x + side * 0.27, (M + gy1) / 2, gz0 + 1.45), v3(side, 0, 0), 0.45, 0.1, teeth=8, spokes=4)
        # the corner post carrying the overhang (the poop deck stops a block short of the gallery's aft face)
        add_cube(bone, "gallery_post_" + sn, (x, (M + P) / 2, oz + 0.25), EYE, (0.5, P - M, 0.5), "iron_band")
        add_cube(bone, "gallery_post_band_" + sn, (x, gy1 + 0.4, oz + 0.25), EYE, (0.56, 0.16, 0.56), "brass")
    add_cube(bone, "gallery_wall_aft", (0, (M + gy1) / 2, gz0 - 0.25), EYE, (gx1 - gx0, gy1 - M, 0.5), "plate_b")
    add_cube(bone, "gallery_cap_aft", (0, gy1 + 0.06, gz0 - 0.25), EYE, (gx1 - gx0 + 0.1, 0.12, 0.6), "copper2")
    add_cube(bone, "gallery_band_aft", (0, M + 0.25, gz0 - 0.51), EYE, (gx1 - gx0 + 1.0, 0.2, 0.04), "brass")
    path = [v3(xw, gy1 + 0.12, gz1), v3(xw, gy1 + 0.12, gz0 - 0.25), v3(-xw, gy1 + 0.12, gz0 - 0.25), v3(-xw, gy1 + 0.12, gz1)]
    railing(bone, "gallery_rail", path, P - gs.SLAB - gy1 - 0.2, every=0.85)
    for side, sn in SIDES:
        lantern(lights, "lantern_gallery_" + sn, v3(side * (xw + 0.32), (M + gy1) / 2 + 0.25, gz0 + 3.0), hang=True, drop=0.12, s=1.1)
        beam(bone, "gallery_lantern_arm_" + sn, v3(side * (xw + 0.2), (M + gy1) / 2 + 0.3, gz0 + 3.0), v3(side * (xw + 0.38), (M + gy1) / 2 + 0.3,
             gz0 + 3.0), 0.08, "iron")
    # the overhang of the poop deck: its slab (planks over, a ceiling under), its fascia, bulwark and cap; it stops at
    # OVERHANG_Z, the gallery's last block standing out beyond it under the sky (as on the reference)
    zo = (oz + TZ) / 2
    lo = TZ - oz
    add_cube(bone, "overhang_deck", (0, P - 0.25, zo), EYE, (gx1 - gx0 + 1.0, 0.5, lo), {"all": "plate_b", "+2": "deck", "-2": "ceil"})
    for side, sn in SIDES:
        add_cube(bone, "overhang_bulwark_" + sn, (side * xw, (P + gs.POOP_CAP_Y) / 2, zo), EYE, (0.5, gs.POOP_CAP_Y - P, lo), "plate_b")
        add_cube(bone, "overhang_cap_" + sn, (side * xw, gs.POOP_CAP_Y + 0.07, zo), EYE, (0.62, 0.14, lo + 0.1), "copper2")
        add_cube(bone, "overhang_fascia_" + sn, (side * (xw + 0.26), P - 0.25, zo), EYE, (0.04, 0.5, lo), "copper")
    add_cube(bone, "overhang_bulwark_aft", (0, (P + gs.POOP_CAP_Y) / 2, oz + 0.25), EYE, (gx1 - gx0, gs.POOP_CAP_Y - P, 0.5), "plate_b")
    add_cube(bone, "overhang_cap_aft", (0, gs.POOP_CAP_Y + 0.07, oz + 0.25), EYE, (gx1 - gx0 + 1.1, 0.14, 0.62), "copper2")
    add_cube(bone, "overhang_fascia_aft", (0, P - 0.25, oz - 0.01), EYE, (gx1 - gx0 + 1.0, 0.5, 0.04), "copper")
    path = [v3(xw, gs.POOP_CAP_Y + 0.14, TZ), v3(xw, gs.POOP_CAP_Y + 0.14, oz + 0.25), v3(-xw, gs.POOP_CAP_Y + 0.14, oz + 0.25),
            v3(-xw, gs.POOP_CAP_Y + 0.14, TZ)]
    railing(bone, "rail_taffrail", path, 1.05, every=0.9, gaps=[(v3(0, P, oz + 0.25), 0.8)])   # the crane stands on the aft edge


def railing(bone, name, path, h, every=1.0, post="wood_dark", rail="rail", gaps=()):
    """The railings of the reference: dark posts with brass caps about a block apart, a top rail and a middle
    rail of copper-brown bars. gaps: (point, half width) where the rails stop (ladders, stairs)."""
    def gapped(p):
        return any(np.linalg.norm((p - g)[[0, 2]]) < hw for g, hw in gaps)
    k = 0
    for i, (a, b) in enumerate(polyline(path)):
        seg = np.linalg.norm(b - a)
        n = max(1, int(round(seg / every)))
        pts = [a + (b - a) * (j / n) for j in range(n + 1)]
        for j in range(n):
            p0, p1 = pts[j], pts[j + 1]
            if gapped((p0 + p1) / 2):
                continue
            beam(bone, "%s_top_%d_%d" % (name, i, j), p0 + v3(0, h, 0), p1 + v3(0, h, 0), 0.13, rail, width=0.17, extend=0.06)
            beam(bone, "%s_mid_%d_%d" % (name, i, j), p0 + v3(0, h * 0.5, 0), p1 + v3(0, h * 0.5, 0), 0.08, rail, width=0.1, extend=0.04)
        for j, p in enumerate(pts if i == len(path) - 2 else pts[:-1]):
            if gapped(p):
                continue
            add_cube(bone, "%s_post_%d" % (name, k), p + v3(0, h / 2, 0), EYE, (0.17, h, 0.17), post)
            add_cube(bone, "%s_post_cap_%d" % (name, k), p + v3(0, h + 0.09, 0), EYE, (0.24, 0.12, 0.24), "brass")
            k += 1


def gear(bone, name, c, axis, r, th, teeth=12, spokes=8, region="gear_bevel"):
    """A brass gear wheel in its own bone "gear_<name>" (origin at its centre, local x along its axle): a rim,
    square teeth, spokes, a hub. The engine animation turns it about its axle. Each piece shows the whole bevelled
    brass bar (1.27.1: lit and shadowed edges, the wheel reads in relief)."""
    st = region == "gear_bevel"
    axis = norm(v3(*axis))
    c = v3(*c)
    gb = Bone(name, origin=tuple(c), rot=gg.frame_from(axis, v3(0, 1, 0) if abs(axis[1]) < 0.9 else v3(0, 0, 1)), parent=bone)
    e1 = norm(np.cross(axis, v3(0, 1, 0) if abs(axis[1]) < 0.9 else v3(1, 0, 0)))
    e2 = np.cross(axis, e1)
    nr = max(12, teeth)
    for k in range(nr):
        a0, a1 = 2 * math.pi * k / nr, 2 * math.pi * (k + 1) / nr
        p0 = c + (e1 * math.cos(a0) + e2 * math.sin(a0)) * r * 0.8
        p1 = c + (e1 * math.cos(a1) + e2 * math.sin(a1)) * r * 0.8
        beam(gb, "%s_rim_%d" % (name, k), p0, p1, r * 0.2, region, width=th, up=np.cross(axis, norm(p1 - p0)), extend=r * 0.03, stretch=st)
    for k in range(teeth):
        a = 2 * math.pi * (k + 0.5) / teeth
        d = e1 * math.cos(a) + e2 * math.sin(a)
        t = np.cross(axis, d)
        add_cube(gb, "%s_tooth_%d" % (name, k), c + d * (r * 0.95), np.column_stack([d, t, axis]), (r * 0.22, 2 * math.pi * r / teeth * 0.45, th * 0.92),
                 region, stretch=st)
    for k in range(spokes):
        a = 2 * math.pi * k / spokes
        d = e1 * math.cos(a) + e2 * math.sin(a)
        beam(gb, "%s_spoke_%d" % (name, k), c + d * r * 0.2, c + d * r * 0.74, th * 0.7, region, width=r * 0.12, up=axis, stretch=st)
    disc(gb, name + "_hub", c, axis, r * 0.22, th * 1.4, "gear_face", n=3)
    disc(gb, name + "_axle", c + axis * th * 0.6, axis, r * 0.08, th * 0.6, "iron_dark", n=2)
    return gb


def cylinder(bone, name, c, h, r, region, n=16, axis=(0, 1, 0), tile=True, inner=None):
    """A round shell of n plates about a vertical (or given) axis from c, h long."""
    axis = norm(v3(*axis))
    c = v3(*c)
    e1 = norm(np.cross(axis, v3(0, 0, 1) if abs(axis[2]) < 0.9 else v3(1, 0, 0)))
    e2 = np.cross(axis, e1)
    w = 2 * r * math.tan(math.pi / n) + 0.01
    cubes = []
    for k in range(n):
        a = 2 * math.pi * (k + 0.5) / n
        d = e1 * math.cos(a) + e2 * math.sin(a)
        t = np.cross(axis, d)
        regs = {"all": region}
        if inner:
            regs["-3"] = inner
        cube = add_cube(bone, "%s_%d" % (name, k), c + axis * (h / 2) + d * (r - 0.05), np.column_stack([t, axis, d]), (w, h, 0.1), regs,
                        u_dir=t, v_dir=-axis)
        if tile:
            lu = min(1.0, w * 16 / 64)
            u0 = (k * lu) % 1.0
            if u0 + lu > 1:
                u0 = 1 - lu
            lv = min(1.0, h * 16 / 32)
            for f, spec in cube.faces.items():
                if spec is not None and spec["region"] == region:
                    spec["sub"] = (u0, 0.0, u0 + lu, lv)
        cubes.append(cube)
    return cubes


def ring(bone, name, c, r, th, h, region, n=16):
    """A flat band round a vertical axis (a brass band on the funnel or the dome)."""
    c = v3(*c)
    w = 2 * r * math.tan(math.pi / n) + 0.02
    for k in range(n):
        a = 2 * math.pi * (k + 0.5) / n
        d = v3(math.cos(a), 0, math.sin(a))
        t = np.cross(v3(0, 1, 0), d)
        add_cube(bone, "%s_%d" % (name, k), c + d * (r + th / 2 - 0.05), np.column_stack([t, v3(0, 1, 0), d]), (w, h, th), region)


def dome_cap(bone, name, cz, prof, region, n=20, top_region=None):
    """A surface of revolution about the vertical axis at (0, cz): prof = [(y, r), ...] from the bottom up, each
    course made of n plates slanted along the meridian (no steps), the top closed by a disc. Each plate shows the
    whole region (one riveted plate: the gores of the dome line up from course to course)."""
    for j in range(len(prof) - 1):
        (ya, ra), (yb, rb) = prof[j], prof[j + 1]
        for k in range(n):
            a = 2 * math.pi * (k + 0.5) / n
            d = v3(math.cos(a), 0, math.sin(a))
            pa, pb = v3(0, ya, cz) + d * (ra - 0.05), v3(0, yb, cz) + d * (rb - 0.05)
            m = norm(pb - pa)
            nrm = norm(np.cross(m, v3(-math.sin(a), 0, math.cos(a))))    # outwards
            t = np.cross(m, nrm)                                         # round the dome (a right-handed frame)
            w = 2 * max(ra, rb) * math.tan(math.pi / n) + 0.02
            add_cube(bone, "%s_%d_%d" % (name, j, k), (pa + pb) / 2, np.column_stack([t, m, nrm]), (w, np.linalg.norm(pb - pa) + 0.06, 0.1),
                     {"all": region, "-3": top_region or region}, u_dir=t, v_dir=-m, stretch=True)
    yt, rt = prof[-1]
    disc(bone, name + "_top", (0, yt - 0.03, cz), (0, 1, 0), rt, 0.06, top_region or region, n=3)


def pipe(bone, name, pts, d=0.6, flange=True):
    """A copper pipe along a polyline, rounded elbows (a block at each bend) and brass flanges."""
    pts = [v3(*p) for p in pts]
    for k in range(len(pts) - 1):
        round_bar(bone, "%s_%d" % (name, k), pts[k], pts[k + 1], d, "pipe", extend=d * 0.15)
    for k, p in enumerate(pts):
        if 0 < k < len(pts) - 1:
            add_cube(bone, "%s_elbow_%d" % (name, k), p, EYE, (d * 1.12, d * 1.12, d * 1.12), "pipe")
            if flange:
                for j, q in enumerate((pts[k - 1], pts[k + 1])):
                    dd = norm(q - p)
                    disc(bone, "%s_flange_%d_%d" % (name, k, j), p + dd * (d * 0.75), dd, d * 0.62, 0.12, "brass", n=3)
        elif flange:
            q = pts[1] if k == 0 else pts[-2]
            dd = norm(p - q)
            disc(bone, "%s_end_%d" % (name, k), p - dd * 0.08, dd, d * 0.65, 0.16, "brass", n=3)


CREW_WINDOWS_Z, CREW_WINDOW_Y = gs.CREW_WINDOWS_Z, gs.CREW_WINDOW_Y
STERN_STRIP_Z, STERN_LADDER_Z, WATER_LADDER_Z = gs.STERN_STRIP_Z, gs.STERN_LADDER_Z, gs.WATER_LADDER_Z
PIPE_LOW_Z, PIPE_ARCH_Z = gs.PIPE_LOW_Z, gs.PIPE_ARCH_Z


def trims(bone, detail):
    """The stepped copper and brass trims along both sides (raised riveted strips), the windows of the hold and
    of the crew quarters in brass frames, the big and the bow gear wheels, the copper pipes, the hull ladders."""
    def strip(name, z0, z1, y, h, region, side, out=0.06):
        zs = [z for z in STATIONS if z0 < z < z1]
        zs = [z0] + zs + [z1]
        for i in range(len(zs) - 1):
            za, zb = zs[i], zs[i + 1]
            if zb - za < 0.05:
                continue
            a, b = hp(za, y, side, out), hp(zb, y, side, out)
            cube = beam(bone, "%s_%d" % (name, i), a, b, h, region, width=0.14, up=v3(0, 1, 0), extend=0.03)
            for spec in cube.faces.values():
                if spec is not None:
                    lu = min(1.0, cube.size[0] * 16 / 64)
                    u0 = ((za - TZ) * 16 % 64) / 64
                    if u0 + lu > 1:
                        u0 = max(0.0, 1 - lu)
                    spec["sub"] = (u0, 0.0, u0 + lu, 1.0)
                    spec["u_dir"], spec["v_dir"] = v3(0, 0, 1), v3(0, -1, 0)

    def riser(name, z, y0, y1, side, w=0.5, region="brass_band"):
        p, u, v, n = side_frame(z, (y0 + y1) / 2, side)
        add_cube(bone, name, p + n * 0.27, np.column_stack([u, v3(0, 1, 0), n]), (w, y1 - y0 + 0.33, 0.14), region, stretch=True,
                 u_dir=v3(0, -1, 0), v_dir=u)

    for side, sn in SIDES:
        # the long copper band low on the hull, the brass band over it amidships, the band rising at the bow
        strip("band_low_" + sn, TZ + 0.1, 10.25, 2.2, 0.42, "copper", side)
        riser("riser_a_" + sn, 6.1, 2.2, 4.5, side)
        strip("band_mid_" + sn, 5.85, 9.6, 4.5, 0.42, "brass_band", side)
        riser("riser_b_" + sn, 9.4, 4.5, 5.3, side)   # clear of the stowed gangplank (z 7.5 -> 8.9)
        riser("riser_c_" + sn, 10.25, 2.2, 3.4, side)
        strip("band_bow_" + sn, 10.0, gs.stem_z(3.4) - 0.6, 3.4, 0.5, "copper", side)
        # the chunky brass piece running forward from the bow gear to the stem, level with the gear's hub
        strip("band_bow2_" + sn, gs.BOW_GEAR[1] + gs.BOW_GEAR[2] + 0.1, gs.stem_z(gs.BOW_GEAR[0]) - 0.5, gs.BOW_GEAR[0], 0.6, "brass_band", side)
        # the stern: brass brackets climbing to the poop cap, a long copper strip by the ladder
        riser("riser_stern_" + sn, STERN_STRIP_Z, 2.4, gs.POOP_CAP_Y - 0.3, side, w=0.36, region="copper")
        riser("riser_stern2_" + sn, -13.9, 0.8, 2.2, side, w=0.4)
        # windows: two in the crew quarters (under the poop), two in the hold (amidships)
        for j, (z, y, w, h) in enumerate([(z, CREW_WINDOW_Y, 1.15, 1.45) for z in CREW_WINDOWS_Z] + [(2.9, 3.0, 1.55, 1.55), (5.0, 3.0, 1.55, 1.55)]):
            hull_decal(bone, "hull_window_%s%d" % (sn, j), z, y, side, w, h, "glow_window", out=0.03, th=0.04, glow=True)
            p, u, v, n = side_frame(z, y, side)
            R = np.column_stack([u, v3(0, 1, 0), n])
            # the frame: a lintel and a deeper sill (1.27.1: they stand out of the plates and catch the light), the jambs
            for k, (du, dv, sw, sh, dn, sd) in enumerate(((0, h / 2 + 0.09, w + 0.4, 0.18, 0.27, 0.14), (0, -h / 2 - 0.09, w + 0.5, 0.18, 0.3, 0.2),
                                                          (w / 2 + 0.08, 0, 0.16, h, 0.245, 0.1), (-w / 2 - 0.08, 0, 0.16, h, 0.245, 0.1))):
                add_cube(detail, "hull_window_frame_%s%d_%d" % (sn, j, k), p + u * du + v3(0, dv, 0) + n * dn, R, (sw, sh, sd), "brass_band")
        # the gear wheels: the big one amidships, the small one at the bow
        y, z, r = gs.BIG_GEAR
        p, u, v, n = side_frame(z, y, side)
        add_cube(detail, "gear_big_mount_" + sn, p + n * 0.08, np.column_stack([u, v3(0, 1, 0), n]), (0.9, 0.9, 0.14), "iron_band")
        gear(bone, "gear_big_" + sn, p + n * 0.24, n, r, 0.24, teeth=12, spokes=8)
        y, z, r = gs.BOW_GEAR
        p, u, v, n = side_frame(z, y, side)
        gear(bone, "gear_bow_" + sn, p + n * 0.2, n, r, 0.2, teeth=10, spokes=8)
        # a flat black iron plate behind it (1.27.1: the lit bevels of the plates were as bright as the gear, which
        # melted into the hull at a distance; on black its spokes and rim read as on the reference)
        disc(bone, "gear_bow_back_" + sn, p + n * 0.06, n, r * 0.86, 0.05, "iron_dark", n=3)
        # the copper pipes: the low run from the stern quarter to the big gear, a pipe down into the sea, the
        # great inverted U on the engine house wall
        o = 0.36
        zg = gs.BIG_GEAR[1] - gs.BIG_GEAR[2] - 0.15
        za, zr = PIPE_LOW_Z
        pipe(bone, "pipe_low_" + sn, [hp(za, 3.9, side, 0.05), hp(za, 3.9, side, o), hp(za + 0.2, 2.7, side, o), hp(zr, 2.7, side, o),
                                     hp(zr, 4.7, side, o), hp(zg, 4.7, side, o)], d=0.7)
        pipe(bone, "pipe_down_" + sn, [hp(zr, 2.7, side, o), hp(zr, -0.4, side, o)], d=0.62, flange=False)
        oo = 0.45
        a0, a1 = PIPE_ARCH_Z
        pipe(bone, "pipe_arch_" + sn, [hp(a0, 6.0, side, oo + 0.1), hp(a0, 8.2, side, oo + 0.1), hp(a1, 8.2, side, oo + 0.1), hp(a1, 6.0, side, oo + 0.1)], d=1.0)
        for j, z in enumerate(PIPE_ARCH_Z):
            p, u, v, n = side_frame(z, 5.9, side)
            add_cube(bone, "pipe_arch_foot_%s%d" % (sn, j), p + n * 0.25, np.column_stack([u, v3(0, 1, 0), n]), (1.0, 0.5, 0.5), "brass_band")
        # a row of brass brackets along the engine house wall under the pipes
        for j, z in enumerate(np.arange(-5.0, 4.6, 1.2)):
            if abs(z - gs.BIG_GEAR[1]) < gs.BIG_GEAR[2] + 0.4 or min(abs(z - a) for a in PIPE_ARCH_Z) < 0.8:
                continue
            p, u, v, n = side_frame(z, 6.05, side)
            add_cube(detail, "engine_bracket_%s%d" % (sn, j), p + n * 0.09, np.column_stack([u, v3(0, 1, 0), n]), (0.45, 0.32, 0.16), "brass")
        # the ladders on the hull side (the rope ladder of the reference and a brass ladder from the water)
        hull_ladder(bone, "ladder_stern_" + sn, STERN_LADDER_Z, 2.4, gs.POOP_CAP_Y + 0.4, side)
        hull_ladder(bone, "ladder_water_" + sn, WATER_LADDER_Z, -0.4, 4.3, side)


def hull_ladder(bone, name, z, y0, y1, side, w=0.8):
    for k, dz in enumerate((-w / 2, w / 2)):
        beam(bone, "%s_rail_%d" % (name, k), hp(z + dz, y0, side, 0.14), hp(z + dz, y1, side, 0.14), 0.12, "wood_dark", width=0.12)
    for j, y in enumerate(np.arange(y0 + 0.3, y1 - 0.1, 0.42)):
        beam(bone, "%s_rung_%d" % (name, j), hp(z - w / 2, y, side, 0.16), hp(z + w / 2, y, side, 0.16), 0.08, "brass", width=0.08)


def bulwarks(bone, detail):
    """The inner faces of the bulwarks and of the engine house roof's edge (on the grid's collision line),
    the riveted caps on them, the railings of the reference on the caps."""
    def inner_lining(name, z0, z1, y0, y1, region="plate_b"):
        zs = [z0] + [z for z in STATIONS if z0 < z < z1] + [z1]
        for side, sn in SIDES:
            for i in range(len(zs) - 1):
                za, zb = zs[i], zs[i + 1]
                if zb - za < 0.05:
                    continue
                a0, a1 = hp(za, y0, side, -0.6), hp(za, y1, side, -0.6)
                b0, b1 = hp(zb, y0, side, -0.6), hp(zb, y1, side, -0.6)
                board(bone, "%s_%s%d" % (name, sn, i), a0, a1, b0, b1, 0.06, region, v3(-side, 0, 0), overlap=1.02)

    def cap(name, z0, z1, y, region="copper2", w=0.72):
        zs = [z0] + [z for z in STATIONS if z0 < z < z1] + [z1]
        for side, sn in SIDES:
            for i in range(len(zs) - 1):
                za, zb = zs[i], zs[i + 1]
                if zb - za < 0.05:
                    continue
                cube = beam(bone, "%s_%s%d" % (name, sn, i), hp(za, y + 0.083, side, -0.27), hp(zb, y + 0.083, side, -0.27), 0.14, region,
                            width=w, extend=0.04)
                for spec in cube.faces.values():
                    if spec is not None:
                        lu = min(1.0, cube.size[0] * 16 / 64)
                        u0 = ((za - TZ) * 16 % 64) / 64
                        spec["sub"] = (u0 if u0 + lu <= 1 else 1 - lu, 0.0, (u0 if u0 + lu <= 1 else 1 - lu) + lu, 1.0)

    def side_rail(name, z0, z1, y, h, gaps=()):
        for side, sn in SIDES:
            zs = [z0] + [z for z in STATIONS if z0 < z < z1] + [z1]
            path = [hp(z, y + 0.14, side, -0.3) for z in zs]
            railing(bone, "%s_%s" % (name, sn), path, h, every=1.0, gaps=[(g, hw) for (g, hw) in gaps if np.sign(g[0]) == side])

    inner_lining("lining_waist", EF, FZ, M, gs.WAIST_CAP_Y)
    inner_lining("lining_fc", FZ, 19.4, F, gs.FORECASTLE_CAP_Y)
    inner_lining("lining_poop", TZ, PF, P, gs.POOP_CAP_Y)
    cap("cap_waist", EF, FZ, gs.WAIST_CAP_Y)
    cap("cap_fc", FZ, 19.4, gs.FORECASTLE_CAP_Y)
    cap("cap_poop", TZ, PF, gs.POOP_CAP_Y)
    cap("cap_engine", PF, EF, E, region="stone", w=0.72)
    # the gangplank's gate in the starboard waist railing
    gate = (v3(-4.6, M, 8.2), 1.45)
    side_rail("rail_waist", EF, FZ, gs.WAIST_CAP_Y, 1.15, gaps=[gate])
    side_rail("rail_fc", FZ, 19.0, gs.FORECASTLE_CAP_Y, 1.15)
    side_rail("rail_poop", TZ, PF, gs.POOP_CAP_Y, 1.05)
    side_rail("rail_engine", PF, EF, E, 0.95)
    # across the engine house front (gaps at the ladders), the forecastle's break (gaps at the stairs)
    xe = gs.hull_x(EF, E) - 0.3
    lad = [(v3(s * sum(gs.ROOF_LADDER_X) / 2, E, EF - 0.25), 0.55) for s in (1, -1)]
    railing(bone, "rail_engine_front", [v3(xe, E, EF - 0.25), v3(-xe, E, EF - 0.25)], 0.95, gaps=lad)
    xf = gs.hull_x(FZ, F) - 0.3
    st = [(v3(s * sum(gs.FC_STAIR_X) / 2, F, FZ + 0.25), 0.8) for s in (1, -1)]
    railing(bone, "rail_fc_break", [v3(xf, F, FZ + 0.25), v3(-xf, F, FZ + 0.25)], 1.05, gaps=st)


def decks(bone):
    """Plank decks: the waist (the companion hatch left open), the forecastle, the poop, the engine house roof
    (round the funnel and the dome, which stand on it); their front edges."""
    def deck(name, z0, z1, y, holes=(), xmax=None):
        zs = list(np.arange(z0, z1 - 0.01, 1.0)) + [z1]
        for j in range(len(zs) - 1):
            za, zb = zs[j], zs[j + 1]
            w = min(gs.hull_x(za, y), gs.hull_x(zb, y)) - 0.55
            if xmax is not None:
                w = min(w, xmax)
            if w < 0.3:
                continue
            spans = [(-w, w)]
            for hx0, hx1, hz0, hz1 in holes:
                if za < hz1 - 1e-6 and zb > hz0 + 1e-6:
                    new = []
                    for a, b in spans:
                        if b <= hx0 or a >= hx1:
                            new.append((a, b))
                        else:
                            if a < hx0:
                                new.append((a, hx0))
                            if b > hx1:
                                new.append((hx1, b))
                    spans = new
            for k, (x0, x1) in enumerate(spans):
                add_cube(bone, "%s_%d_%d" % (name, j, k), ((x0 + x1) / 2, y - 0.08, (za + zb) / 2), DECK_AXES, (zb - za + 0.01, 0.16, x1 - x0),
                         {"all": "deck", "-2": "dark_wood"})
    deck("deck_waist", EF, FZ, M, holes=[(gs.COMPANION_X[0], gs.COMPANION_X[1], gs.COMPANION_Z[0], gs.COMPANION_Z[1])])
    deck("deck_fc", FZ, 19.5, F)
    deck("deck_poop", TZ + 0.25, PF, P)
    deck("deck_engine", PF, EF - 0.5, E)
    deck("deck_bridge", DZ0, gs.BRIDGE_FRONT_Z + 0.5, B, xmax=DH)
    # the front of the forecastle deck (its riser over the waist), the engine house front wall (with the door)
    xf = gs.hull_x(FZ, F) - 0.5
    add_cube(bone, "fc_break", (0, (M + F) / 2, FZ + 0.25), EYE, (2 * xf, F - M, 0.5), {"all": "plate_b", "+2": "deck"})
    xe = gs.hull_x(EF, E) - 0.05
    dx0, dx1, dy0, dy1 = -0.75, 0.75, M, M + 2.5
    for k, (x0, x1, y0, y1) in enumerate(((-xe, dx0, M, E), (dx1, xe, M, E), (dx0, dx1, dy1, E))):
        add_cube(bone, "engine_front_%d" % k, ((x0 + x1) / 2, (y0 + y1) / 2, EF - 0.25), EYE, (x1 - x0, y1 - y0, 0.5),
                 {"all": "plate_b", "-3": "wall_iron"})
    add_cube(bone, "engine_front_band", (0, E - 0.25, EF + 0.01), EYE, (2 * xe, 0.5, 0.04), "stone")
    add_cube(bone, "engine_front_plaque", (0, M + 2.95, EF + 0.03), EYE, (1.4, 0.36, 0.04), "plaque", stretch=True)


WIN_Y = gs.CABIN_WINDOW_Y     # the centre of the deckhouse windows (tools/gear_steam_decor.py draws them from inside)


DECKHOUSE_WINDOWS_Z = gs.DECKHOUSE_WINDOWS_Z


def deckhouse(bone, lights):
    """The captain's deckhouse on the poop deck (plated walls, a dark riveted course under the roof, three lit
    windows a side in brass frames, the door and the ladder aft) and the bridge on its roof (railing, the helm,
    lanterns). Its fore part stands on the engine house roof and wraps the funnel, which rises through it (as on the
    reference, where the funnel stands at the deckhouse's fore end): the cabin's front wall is the aft face of that
    casing, and the casing's top is closed off by a railing across the bridge before the funnel."""
    h1 = B
    zc = (DZ0 + DZ1) / 2
    parts = ((DZ0, PF, P), (PF, DZ1, E))     # (z0, z1, foot): on the poop deck, then on the engine house roof
    for side, sn in SIDES:
        for q, (za, zb, y0) in enumerate(parts):
            add_cube(bone, "deckhouse_wall_%s%d" % (sn, q), (side * (DH - 0.25), (y0 + h1) / 2, (za + zb) / 2), EYE, (0.5, h1 - y0, zb - za),
                     {"all": "plate_b", ("-1" if side > 0 else "+1"): "wall_wood"})
            add_cube(bone, "deckhouse_foot_%s%d" % (sn, q), (side * (DH + 0.01), y0 + 0.1, (za + zb) / 2), EYE, (0.05, 0.2, zb - za), "copper")
        add_cube(bone, "deckhouse_course_" + sn, (side * (DH + 0.01), h1 - 0.15, zc), EYE, (0.04, 0.3, DZ1 - DZ0), "stone")
        for j, z in enumerate(DECKHOUSE_WINDOWS_Z):
            # the big lit windows of the reference, standing clear above the poop railing
            add_cube(bone, "glow_deckhouse_window_%s%d" % (sn, j), (side * (DH + 0.02), WIN_Y, z), EYE, (0.04, 1.5, 1.25), "glow_window", stretch=True,
                     u_dir=v3(0, 0, -side), v_dir=v3(0, -1, 0))
            for k, (dy, dz, sy, sz, dx, sx) in enumerate(((0.84, 0, 0.18, 1.6, 0.08, 0.16), (-0.85, 0, 0.18, 1.75, 0.12, 0.24),
                                                          (0, 0.7, 1.5, 0.16, 0.06, 0.12), (0, -0.7, 1.5, 0.16, 0.06, 0.12))):
                add_cube(bone, "deckhouse_window_frame_%s%d_%d" % (sn, j, k), (side * (DH + dx), WIN_Y + dy, z + dz), EYE, (sx, sy, sz), "brass_band")
    # the front wall, on the engine house roof, split round the funnel (a small lit window each side of it)
    fz, fr = gs.FUNNEL_Z, gs.FUNNEL_R
    zf = DZ1 - 0.25
    xg = math.sqrt(max(0.0, (fr + 0.02) ** 2 - (zf - fz) ** 2)) - 0.05
    for side, sn in SIDES:
        x0, x1 = xg, DH - 0.5
        add_cube(bone, "deckhouse_front_" + sn, (side * (x0 + x1) / 2, (E + h1) / 2, zf), EYE, (x1 - x0, h1 - E, 0.5), "plate_b")
        add_cube(bone, "glow_deckhouse_fwd_window_" + sn, (side * 2.05, WIN_Y + 0.05, DZ1 + 0.02), EYE, (0.62, 1.1, 0.04), "glow_window", stretch=True)
        add_cube(bone, "deckhouse_course_f" + sn, (side * (xg + DH) / 2, h1 - 0.15, DZ1 + 0.01), EYE, (DH - xg, 0.3, 0.04), "stone")
        add_cube(bone, "deckhouse_foot_f" + sn, (side * (xg + DH) / 2, E + 0.1, DZ1 + 0.01), EYE, (DH - xg, 0.2, 0.05), "copper")
    # the aft wall (the door, the ladder, a window)
    z = DZ0 + 0.25
    d0, d1, dy1 = -1.25, 0.25, P + 2.5
    for j, (x0, x1, y0, y1) in enumerate(((-DH + 0.5, d0, P, h1), (d1, DH - 0.5, P, h1), (d0, d1, dy1, h1))):
        add_cube(bone, "deckhouse_aft_%d" % j, ((x0 + x1) / 2, (y0 + y1) / 2, z), EYE, (x1 - x0, y1 - y0, 0.5), {"all": "plate_b", "+3": "wall_wood"})
    add_cube(bone, "glow_deckhouse_aft_window", (-2.1, 9.4, z - 0.27), EYE, (0.8, 0.9, 0.04), "glow_window", stretch=True)
    add_cube(bone, "deckhouse_course_1", (0, h1 - 0.15, z - 0.26), EYE, (2 * DH, 0.3, 0.04), "stone")
    # the roof's riveted edge: a frame round the bridge
    for side, sn in SIDES:
        add_cube(bone, "deckhouse_roof_edge_" + sn, (side * (DH - 0.15), B + 0.04, zc), EYE, (0.5, 0.08, DZ1 - DZ0 + 0.2), "stone")
    for k, zz in enumerate((DZ0 + 0.15, DZ1 - 0.15)):
        add_cube(bone, "deckhouse_roof_edge_%d" % k, (0, B + 0.04, zz), EYE, (2 * DH - 0.6, 0.08, 0.5), "stone")
    # the casing's top beside the funnel (closed off; plates), and the railing across the bridge before it
    zb0 = gs.BRIDGE_FRONT_Z
    zc0 = zb0 + 0.5
    add_cube(bone, "casing_top", (0, B + 0.03, (zc0 + DZ1 - 0.3) / 2), EYE, (2 * DH - 0.8, 0.06, DZ1 - 0.3 - zc0), "plate_b")
    # the bridge railing (a gap over the ladder), across before the funnel casing, its lanterns
    lg = [(v3(sum(gs.BRIDGE_LADDER_X) / 2, B, DZ0 + 0.25), 0.55)]
    zr = zb0 + 0.25
    path = [v3(DH - 0.25, B, zr), v3(DH - 0.25, B, DZ0 + 0.25), v3(-DH + 0.25, B, DZ0 + 0.25), v3(-DH + 0.25, B, zr), v3(DH - 0.25, B, zr)]
    railing(bone, "rail_bridge", path, 1.0, every=1.0, gaps=lg)
    for side, sn in SIDES:
        path = [v3(side * (DH - 0.25), B, zr), v3(side * (DH - 0.25), B, DZ1 - 0.25), v3(side * (xg + 0.1), B, DZ1 - 0.25)]
        railing(bone, "rail_casing_" + sn, path, 1.0, every=1.0)
        add_cube(bone, "bridge_lamp_post_" + sn, (side * (DH - 0.25), B + 1.25, -9.25), EYE, (0.18, 0.5, 0.18), "wood_dark")
        lantern(lights, "lantern_bridge_" + sn, v3(side * (DH - 0.25), B + 1.5, -9.25), hang=False, s=1.2)
    # the ladder up to the bridge on the aft wall
    x0, x1 = gs.BRIDGE_LADDER_X
    wall_ladder(bone, "ladder_bridge", (x0 + 0.1, x1 - 0.1), DZ0 - 0.12, P, B + 1.0, along_x=True)


def wall_ladder(bone, name, xs, z, y0, y1, along_x=True):
    for k, x in enumerate(xs):
        add_cube(bone, "%s_rail_%d" % (name, k), (x, (y0 + y1) / 2, z), EYE, (0.12, y1 - y0, 0.12), "wood_dark")
    for j, y in enumerate(np.arange(y0 + 0.4, y1 - 0.05, 0.5)):
        add_cube(bone, "%s_rung_%d" % (name, j), ((xs[0] + xs[1]) / 2, y, z), EYE, (abs(xs[1] - xs[0]), 0.08, 0.08), "brass")


def engine_house(bone, lights, fittings):
    """On the engine house roof: the funnel (riveted black plates, a brass band, a flared cap with a copper
    rim, its uptake pipe), the copper dome on its drum (brass bands and ribs, a railed lookout ring on top),
    clusters of brass gears beside the funnel, the ladders up from the waist, lanterns."""
    fz, fr, ft = gs.FUNNEL_Z, gs.FUNNEL_R, gs.FUNNEL_TOP
    cylinder(bone, "funnel", (0, E, fz), ft - 0.5 - E, fr, "funnel", n=16)
    ring(bone, "funnel_band", (0, 14.35, fz), fr, 0.1, 0.9, "brass_band")
    ring(bone, "funnel_band_low", (0, E + 0.3, fz), fr, 0.12, 0.5, "copper2")
    # the cap, in two flared tiers as on the reference (a broad riveted crown over a narrower collar), copper rims
    cylinder(bone, "funnel_collar", (0, ft - 1.25, fz), 0.7, fr + 0.16, "funnel", n=16, inner="iron_dark")
    ring(bone, "funnel_collar_rim", (0, ft - 0.6, fz), fr + 0.16, 0.12, 0.14, "copper2")
    cylinder(bone, "funnel_cap", (0, ft - 0.55, fz), 0.55, fr + 0.36, "funnel", n=16, inner="iron_dark")
    disc(bone, "funnel_cap_floor", (0, ft - 0.62, fz), (0, 1, 0), fr + 0.36, 0.06, "funnel", n=3)
    ring(bone, "funnel_rim", (0, ft - 0.08, fz), fr + 0.36, 0.12, 0.16, "copper2")
    disc(bone, "funnel_soot", (0, ft - 0.6, fz), (0, 1, 0), fr - 0.05, 0.04, "iron_dark", n=3)
    pipe(bone, "funnel_uptake", [(-1.75, B + 0.03, gs.BRIDGE_FRONT_Z + 0.75), (-1.75, 13.3, gs.BRIDGE_FRONT_Z + 0.75), (-0.95, 13.3, fz - 0.95)], d=0.5)
    # the dome
    dz, dr = gs.DOME_Z, gs.DOME_R
    # 1.27.1: the cap is taller and rounder (a superellipse, its shoulder fuller) on a drum 0.2 lower, the top unchanged;
    # thick brass bands at the foot of the cap and round the lookout ring, as on the reference
    y0 = 12.2
    cylinder(bone, "dome_drum", (0, E, dz), y0 - E, dr - 0.08, "dome_drum", n=16)   # darker than the cap, as on the reference
    ring(bone, "dome_band_base", (0, E + 0.15, dz), dr - 0.08, 0.14, 0.34, "brass_band")
    ring(bone, "dome_band_top", (0, y0 - 0.3, dz), dr - 0.02, 0.24, 0.72, "brass_band")
    for k in range(8):
        a = 2 * math.pi * k / 8
        d = v3(math.cos(a), 0, math.sin(a))
        add_cube(bone, "dome_rib_%d" % k, v3(0, (E + y0) / 2, dz) + d * (dr - 0.03), ry(-a + math.pi / 2), (0.24, y0 - E, 0.14), "brass")
    # the cap: a smooth rounded dome of slanted riveted plates (a superellipse of revolution, 7 courses of 20 plates up
    # to the lookout ring, each plate a gore with its rivets), its 8 brass ribs following the curve
    r_top, pw = 1.45, 2.4
    hd = (gs.DOME_TOP + 0.02 - y0) / (1 - (r_top / dr) ** pw) ** (1 / pw)
    th_max = math.acos((r_top / dr) ** (pw / 2))
    prof = [(y0 + hd * math.sin(f) ** (2 / pw), dr * math.cos(f) ** (2 / pw)) for f in np.linspace(0.0, th_max, 8)]
    dome_cap(bone, "dome_cap", dz, prof, "dome_gore", n=20, top_region="dome")
    ring(bone, "dome_band_crown", (0, prof[-1][0] - 0.12, dz), r_top + 0.02, 0.2, 0.3, "brass_band")
    for k in range(8):
        a = 2 * math.pi * k / 8
        d = v3(math.cos(a), 0, math.sin(a))
        pts = [v3(0, y, dz) + d * (r + 0.07) for y, r in prof]
        for j in range(len(pts) - 1):
            beam(bone, "dome_cap_rib_%d_%d" % (k, j), pts[j], pts[j + 1], 0.1, "brass", width=0.16, extend=0.05)
    disc(bone, "dome_lookout_floor", (0, 14.24, dz), (0, 1, 0), 1.55, 0.1, "dark_wood", n=3)
    n = 10
    ring_pts = [v3(1.45 * math.cos(2 * math.pi * k / n), 14.28, dz + 1.45 * math.sin(2 * math.pi * k / n)) for k in range(n + 1)]
    railing(bone, "dome_rail", ring_pts, 0.85, every=0.95)
    for side, sn in SIDES:
        lantern(lights, "lantern_dome" + ("" if side > 0 else "_s"), v3(side * (dr + 0.25), 10.9, dz - 1.4), hang=True, drop=0.15, s=1.0)
        beam(bone, "dome_lantern_arm_" + sn, v3(side * (dr - 0.1), 11.05, dz - 1.4), v3(side * (dr + 0.3), 11.05, dz - 1.4), 0.08, "iron")
    # the gears beside the funnel (meshing, turning)
    for side, sn in SIDES:
        x = side * (fr + 0.12)
        gear(bone, "gear_funnel_a_" + sn, v3(x, 12.4, fz + 1.1), v3(side, 0, 0), 0.8, 0.16, teeth=10, spokes=6)
        gear(bone, "gear_funnel_b_" + sn, v3(x + side * 0.1, 10.6, fz + 2.15), v3(side, 0, 0), 0.65, 0.16, teeth=9, spokes=6)
        gear(bone, "gear_funnel_c_" + sn, v3(x, 13.9, fz - 0.6), v3(side, 0, 0), 0.55, 0.14, teeth=8, spokes=4)
        add_cube(bone, "gear_funnel_frame_" + sn, (x - side * 0.05, 11.6, fz + 1.2), EYE, (0.12, 3.4, 0.24), "iron_band")
    # the ladders up from the waist on the front wall
    for s in (1, -1):
        xs = sorted((s * (gs.ROOF_LADDER_X[0] + 0.1), s * (gs.ROOF_LADDER_X[1] - 0.1)))
        wall_ladder(bone, "ladder_roof_%s" % ("p" if s > 0 else "s"), xs, EF + 0.12, M, E + 1.0)
    # lanterns on the roof corners
    for side, sn in SIDES:
        x = side * (gs.hull_x(EF, E) - 0.3)
        add_cube(bone, "roof_lamp_post_" + sn, (x, E + 1.2, EF - 0.4), EYE, (0.18, 0.5, 0.18), "wood_dark")
        lantern(lights, "lantern_roof_" + sn, v3(x, E + 1.45, EF - 0.4), hang=False, s=1.2)


# ---------------------------------------------------------------- masts, yards, sails, rigging
MASTS = {
    # name: (z, foot, deck, top, diameter, lookout box (y0, y1, size))
    "main": (gs.MAIN_MAST_Z, H - 0.4, M, gs.MAIN_MAST_TOP, 0.95, (18.5, 20.0, 1.5)),
    "mizzen": (gs.MIZZEN_Z, P, P, gs.MIZZEN_TOP, 0.75, (16.9, 18.1, 1.15)),
}
SQUARE_SAILS = [
    # mast, name, yard y, yard half, sail head along the yard (aft x, fore x), foot inset (aft, fore), drop (aft, fore),
    # bulge of the foot at its fore corner, belly, texture region. As on the reference the sails HANG from their
    # peaked yards: the luffs and leeches are vertical (not the yard's slant), the head follows the yard, the main
    # sail fills the fore part of its yard (a bare yard arm aft of the luff), the foot rounds down at the fore clew;
    # the mizzen sail is deep at its luff and short at its leech
    ("main", "main_sail", gs.MAIN_YARD_Y, gs.MAIN_YARD_HALF, (-3.6, 5.85), (0.3, 0.15), (6.6, 5.9), 0.55, 1.3, "main_sail"),
    ("mizzen", "mizzen_sail", gs.MIZZEN_YARD_Y, gs.MIZZEN_YARD_HALF, (-1.75, 3.25), (0.1, 0.2), (4.3, 2.4), 0.2, 0.6, "mizzen_sail"),
]
FURL_SCALE = {}    # sail bone name -> its x scale once furled (the hanging sail gathered along its own part of the yard)


def mast(root, fittings, name):
    z, foot, deck, head, d, (b0, b1, bs) = MASTS[name]
    mb = Bone("mast_" + name, origin=(0, deck, z), parent=root)
    if foot < deck:
        round_bar(fittings, "lit_mast_%s_below" % name, (0, foot, z), (0, deck, z), d + 0.05, "mast")
    round_bar(mb, name + "_mast", (0, deck - 0.1, z), (0, b1 - 0.1, z), d, "mast")
    add_cube(mb, name + "_partners", (0, deck + 0.15, z), EYE, (d + 0.4, 0.3, d + 0.4), "brass_band")
    bands = (8.5, 13.0, 17.0) if name == "main" else (10.0, 14.0)
    for k, y in enumerate(bands):
        big = k == 0 and name == "main"   # the broad brass collar of the reference, level with the engine house roof
        add_cube(mb, "%s_band_%d" % (name, k), (0, y, z), EYE, (d + (0.55 if big else 0.22), 0.6 if big else 0.24, d + (0.55 if big else 0.22)),
                 "brass_band")
    # the lookout box at the masthead: a dark frame with brass corners and a cap, lit inside
    s = bs
    add_cube(mb, name + "_box_floor", (0, b0 + 0.06, z), EYE, (s, 0.12, s), "dark_wood")
    add_cube(mb, name + "_box_roof", (0, b1 - 0.08, z), EYE, (s + 0.16, 0.16, s + 0.16), "brass_band")
    add_cube(mb, name + "_box_knob", (0, b1 + 0.12, z), EYE, (0.3, 0.24, 0.3), "brass")
    for k, (sx, sz) in enumerate(((1, 1), (1, -1), (-1, 1), (-1, -1))):
        add_cube(mb, "%s_box_post_%d" % (name, k), (sx * (s / 2 - 0.07), (b0 + b1) / 2, z + sz * (s / 2 - 0.07)), EYE, (0.14, b1 - b0, 0.14), "brass")
    for k, (sx, sz) in enumerate(((1, 0), (-1, 0), (0, 1), (0, -1))):
        add_cube(mb, "%s_box_rail_%d" % (name, k), (sx * (s / 2 - 0.05), b0 + 0.45, z + sz * (s / 2 - 0.05)), EYE,
                 (0.1 if sx else s, 0.5, s if sx else 0.1), "wood_dark")
    add_cube(mb, "glow_%s_box_light" % name, (0, (b0 + b1) / 2 + 0.15, z), EYE, (s * 0.4, (b1 - b0) * 0.35, s * 0.4), "glow")
    return mb


def hanging_sail(z, zz, y_top, head, inset, drop, bulge, belly):
    """P(s, t) of a sail hanging from a peaked yard, in the frame of the yard before its peak and brace (yard_rot):
    s across from the aft luff (0) to the fore leech (1), t down from the head. The head runs along the yard,
    the sides drop vertically once the yard is peaked (TILT), the foot bulges down near the fore clew."""
    c, sn = math.cos(TILT), math.sin(TILT)
    xa, xb = head
    ia, ib = inset
    da, db = drop

    def P_(s, t):
        xh = xa + (xb - xa) * s
        # the head, just under the yard, in the vertical plane of the yard (u along it, w up), about the sling
        uh, wh = xh * c - 0.14 * sn, -xh * sn - 0.14 * c
        uf = uh + ia * c * (1 - s) - ib * c * s
        d = da + (db - da) * s + bulge * math.sin(math.pi * s ** 3)
        u = uh + (uf - uh) * t
        w = wh - d * t * (1 + 0.05 * t * (1 - (2 * s - 1) ** 2))
        bel = belly * math.sin(math.pi * min(1.0, t * 0.78)) * (0.35 + 0.65 * (1 - (2 * s - 1) ** 2))
        # back to the yard's frame: the peak (rz(-TILT)) puts these sides upright
        return v3(u * c - w * sn, y_top + u * sn + w * c, zz + 0.05 + bel)
    return P_


def square_sail(mb, sails_info, name, z, y_top, yard_half, head, inset, drop, bulge, belly, region, off=0.5):
    """Yard (braced round, starboard arm aft, peaked) and the black sail hanging from it, billowed forward."""
    br = Bone("brace_" + name, origin=(0, y_top, z), parent=mb)
    zz = z + off
    round_bar(br, name + "_yard", (-yard_half, y_top, zz), (yard_half, y_top, zz), 0.3, "mast", extend=0.05)
    for sx in (1, -1):
        add_cube(br, "%s_yardarm_%d" % (name, sx > 0), (sx * (yard_half - 0.1), y_top, zz), EYE, (0.18, 0.38, 0.38), "brass")
        add_cube(br, "%s_yardband_%d" % (name, sx > 0), (sx * yard_half * 0.5, y_top, zz), EYE, (0.14, 0.36, 0.36), "iron_band")
    add_cube(br, name + "_sling", (0, y_top, zz - 0.1), EYE, (0.42, 0.4, 0.4), "iron_band")
    xa, xb = head
    beam(br, name + "_roll", (xa + 0.1, y_top - 0.24, zz + 0.05), (xb - 0.1, y_top - 0.24, zz + 0.05), 0.26, "cloth_roll")
    P_ = hanging_sail(z, zz, y_top, head, inset, drop, bulge, belly)
    # furled (sail_furl scales the sail bone (sx, 0, 0) about its origin): every point goes up to the yard (y_top in
    # this frame) and the hanging sail, whose foot reaches further along the yard than its head, is gathered back
    # between its luff and its leech: the origin on the luff, sx = the head's length over the sail's reach
    reach = max(P_(i / 10, j / 10)[0] for i in range(11) for j in range(11))
    sb = Bone("sail_" + name, origin=(xa, y_top, zz), parent=br)
    FURL_SCALE[sb.name] = round((xb - xa) / (reach - xa), 4)
    cols, rows = gt.SAIL_CELLS[region]
    hanging_patch(sb, name, P_, region, cols, rows)
    sails_info.append((sb, False))
    br.rot = yard_rot()
    return br, P_


def hanging_patch(bone, name, P_, region, nx, ny, th=0.035, overlap=0.03):
    """The cloths of a hanging sail: columns of upright cells (vertical sides, level heads and feet once the yard
    is peaked), stacked down each column, so that the gold stripe and the leech stay straight while the head and
    the foot step along the yard like the blocky cloths of the reference. Each cell maps its own part of the
    texture region; the texture paints the gear emblem through gt.SAIL_COLUMNS (each column's world height span)
    so that it stays round on the slanted cloth."""
    up = v3(-math.sin(TILT), math.cos(TILT), 0)       # the world's vertical in the yard's frame (before the peak)
    spans = []
    for i in range(nx):
        s0, s1, sc = i / nx, (i + 1) / nx, (i + 0.5) / nx
        for j in range(ny):
            t0, t1 = j / ny, (j + 1) / ny
            a0, a1, b0, b1 = P_(s0, t1), P_(s0, t0), P_(s1, t1), P_(s1, t0)
            n = norm(np.cross(b1 - a0, a1 - b0))
            if n[2] < 0:
                n = -n
            v = norm(up - (up @ n) * n)
            u = np.cross(v, n)
            if u @ (b0 + b1 - a0 - a1) < 0:
                u = -u
                v = np.cross(n, u)
            top, bot = P_(sc, t0), P_(sc, t1)
            c = (top + bot) / 2
            Lu = abs((b0 + b1 - a0 - a1) @ u) / 2
            Hv = abs((top - bot) @ v)
            axes = np.column_stack([u, v, n])
            if np.linalg.det(axes) < 0:
                axes[:, 2] = -axes[:, 2]
            cube = add_cube(bone, "%s_%d_%d" % (name, i, j), c, axes, (Lu + overlap, Hv + overlap, th),
                            {"all": None, "+3": region, "-3": region}, stretch=True, u_dir=u, v_dir=-v)
            gn.set_sub(cube, (s0, t0, s1, t1))
        top, bot = P_(sc, 0.0), P_(sc, 1.0)
        spans.append((float(top @ up), float(bot @ up)))
    horiz = np.cross(up, v3(0, 0, 1))
    gt.SAIL_COLUMNS[region] = (spans, float(abs((P_(1.0, 0.5) - P_(0.0, 0.5)) @ horiz)))


def yard_rot():
    """The yards are braced round (the starboard arms aft) and peaked (the aft arm higher), as on the
    reference where the sails show their faces to starboard, their heads and feet slanting down forward."""
    return ry(-BRACE) @ gg.rz(-TILT)


TILT = math.radians(gs.YARD_TILT_DEG)


def braced(p, mast_z, y0):
    """A point of a yard (or its sail) carried round by the brace and the peak about the yard's sling (0, y0, mast_z)."""
    p = v3(*p) - v3(0, y0, mast_z)
    return yard_rot() @ p + v3(0, y0, mast_z)


def sails(root, masts, sails_info):
    yards = {}
    for mast_name, name, yt, yh, head, inset, drop, bulge, bel, reg in SQUARE_SAILS:
        z = MASTS[mast_name][0]
        d = MASTS[mast_name][4]
        _, P_ = square_sail(masts[mast_name], sails_info, name, z, yt, yh, head, inset, drop, bulge, bel, reg, off=d / 2 + 0.2)
        # the clews (aft, fore) in the world, where the sheets are made fast
        clews = {-1: braced(P_(0.0, 1.0), z, yt), 1: braced(P_(1.0, 1.0), z, yt)}
        yards[name] = (z, d / 2 + 0.2, yt, yh, clews)
    return yards


def chain(bone, name, a, b, s=0.2, step=0.24):
    """A chain of the reference: small blocks stepping along the line (a pixelated diagonal)."""
    a, b = v3(*a), v3(*b)
    L = np.linalg.norm(b - a)
    n = max(2, int(L / step))
    for k in range(n + 1):
        p = a + (b - a) * (k / n)
        add_cube(bone, "%s_%d" % (name, k), p, EYE, (s, s, s), "chain")


def chain_ladder(bone, name, tops, feet, step=0.55):
    for k, (a, b) in enumerate(zip(tops, feet)):
        chain(bone, "%s_rail_%d" % (name, k), a, b)
    h = min(a[1] for a in tops) - max(b[1] for b in feet)
    n = int(h / step)
    for j in range(1, n):
        t = j / n
        pa = feet[0] + (tops[0] - feet[0]) * t
        pb = feet[-1] + (tops[-1] - feet[-1]) * t
        beam(bone, "%s_rung_%d" % (name, j), pa, pb, 0.1, "chain", width=0.14, extend=0.05)


def rigging(bone, yards):
    """Chain shrouds as ladders (the dark stepped chains of the reference): the main mast's down aft to the
    engine house roof railing and forward to the forecastle, the mizzen's to the poop railing; stays to the
    prow head, the bridge and the dome; braces and sheets."""
    mz, mtop = gs.MAIN_MAST_Z, MASTS["main"][5][0] - 0.2
    zz, ztop = gs.MIZZEN_Z, MASTS["mizzen"][5][0] - 0.2
    for side, sn in SIDES:
        tops = [v3(side * 0.5, mtop, mz - 0.2), v3(side * 0.52, mtop - 0.3, mz - 0.45)]
        feet = [v3(side * (gs.hull_x(3.4, E) - 0.35), gs.ENGINE_RAIL_TOP, 3.4), v3(side * (gs.hull_x(2.4, E) - 0.35), gs.ENGINE_RAIL_TOP, 2.4)]
        chain_ladder(bone, "main_shroud_" + sn, tops, feet)
        tops = [v3(side * 0.5, mtop - 0.5, mz + 0.3)]
        zf = 16.0
        feet = [v3(side * (gs.hull_x(zf, F) - 0.4), gs.FORECASTLE_CAP_Y + 1.2, zf)]
        chain(bone, "main_fwd_shroud_" + sn, tops[0], feet[0])
        tops = [v3(side * 0.42, ztop, zz - 0.15), v3(side * 0.44, ztop - 0.3, zz - 0.4)]
        feet = [v3(side * (gs.hull_x(TZ + 0.6, P) - 0.35), gs.POOP_CAP_Y + 1.1, TZ + 0.6), v3(side * (gs.hull_x(TZ + 1.3, P) - 0.35), gs.POOP_CAP_Y + 1.1,
                                                                                           TZ + 1.3)]
        chain_ladder(bone, "mizzen_shroud_" + sn, tops, feet)
    ropes = [
        ("forestay", v3(0, mtop + 0.4, mz + 0.4), v3(0, gs.STEM_HEAD[1] + 0.1, gs.stem_z(7.0) - 0.4)),
        ("main_stay_aft", v3(0, mtop - 0.6, mz - 0.4), v3(0, 14.3, gs.DOME_Z + 1.4)),
        ("mizzen_stay", v3(0, ztop + 0.2, zz + 0.4), v3(0, gs.BRIDGE_RAIL_TOP, DZ0 + 0.3)),
        ("crane_stay", v3(0, ztop - 1.0, zz - 0.4), v3(0, gs.CRANE_TIP[1] + 1.0, gs.CRANE_Z + 0.3)),
    ]
    for name, a, b in ropes:
        chain(bone, "chain_" + name, a, b, s=0.18, step=0.26)
    for side, sn in SIDES:
        for name, (z, off, yt, yh, clews) in yards.items():
            arm = braced((side * (yh - 0.2), yt, z + off), z, yt)
            clew = clews[side] + v3(0, 0.1, 0)
            if name == "main_sail":
                # the braces are chains, as the bold stepped chains of the reference: the aft arm's down to the dome's
                # lookout ring, the fore arm's down to the forecastle
                chain(bone, "brace_chain_%s_%s" % (name, sn), arm, v3(side * 1.0, 14.75, gs.DOME_Z + 0.9) if side < 0 else
                      v3(side * (gs.hull_x(14.5, F) - 0.4), gs.FORECASTLE_CAP_Y + 1.2, 14.5), s=0.24, step=0.27)
                beam(bone, "sheet_%s_%s" % (name, sn), clew, v3(side * (gs.hull_x(10.5, M) - 0.4), gs.WAIST_CAP_Y + 1.2, 10.5), 0.06, "rope")
            else:
                beam(bone, "brace_rope_%s_%s" % (name, sn), arm, v3(side * (DH - 0.3), B + 1.0, DZ0 + 0.5), 0.06, "rope")
                beam(bone, "sheet_%s_%s" % (name, sn), clew, v3(side * (gs.hull_x(-13.0, P) - 0.4), gs.POOP_CAP_Y + 1.1, -13.8), 0.06, "rope")


def crane(bone, root):
    """The stern crane, as on the reference: a tall riveted pedestal standing on the poop deck's aft edge (brass
    bands, a broad capital, a lit lamp on each side), the dark post above it with a slewing head, the jib reaching
    level over the stern (a riveted top girder and a raking strut from low on the post, braced between them, brass
    bolts), a pulley at its tip, two chains and the crate hanging from them."""
    cz = gs.CRANE_Z
    bt = gs.CRANE_BASE_TOP
    tip = v3(*gs.CRANE_TIP)
    # the pedestal
    add_cube(bone, "crane_base", (0, (P + bt) / 2, cz), EYE, (1.2, bt - P, 1.2), {"all": "plate_b", "+2": "iron"})
    for k, y in enumerate((P + 0.12, P + 1.05)):
        add_cube(bone, "crane_base_band_%d" % k, (0, y, cz), EYE, (1.28, 0.2, 1.28), "brass_band")
    add_cube(bone, "crane_base_trim", (0, bt - 0.07, cz), EYE, (1.42, 0.14, 1.42), "copper2")
    add_cube(bone, "crane_base_cap", (0, bt + 0.12, cz), EYE, (1.62, 0.26, 1.62), "stone")
    for side, sn in SIDES:
        add_cube(bone, "glow_crane_lamp_" + sn, (side * 0.62, P + 1.55, cz), EYE, (0.03, 0.42, 0.42), "glow_window", stretch=True)
    # the post and its head
    yt = tip[1] + 0.35                  # the top girder, level
    yh = yt + 0.25
    add_cube(bone, "crane_post", (0, (bt + yh) / 2, cz), EYE, (0.98, yh - bt, 0.98), "wood_dark")
    for k, y in enumerate((bt + 0.9, yt - 1.4)):
        add_cube(bone, "crane_post_band_%d" % k, (0, y, cz), EYE, (1.1, 0.22, 1.1), "brass_band")
    add_cube(bone, "crane_head", (0, yh + 0.1, cz + 0.05), EYE, (1.2, 0.7, 1.3), "iron_band")
    add_cube(bone, "crane_king", (0, yh + 0.75, cz + 0.2), EYE, (0.36, 0.8, 0.36), "wood_dark")
    add_cube(bone, "crane_king_cap", (0, yh + 1.2, cz + 0.2), EYE, (0.44, 0.14, 0.44), "brass_band")
    gear(bone, "gear_crane", v3(-0.62, yh + 0.05, cz + 0.05), v3(-1, 0, 0), 0.42, 0.12, teeth=8, spokes=4)
    # the jib: a level top girder (two riveted chords) from the head to the tip, a raking strut from low on the post up to
    # the girder near the tip, braces between them
    t0, t1 = v3(0, yt, cz - 0.3), v3(0, yt, tip[2] - 0.2)
    s0, s1 = v3(0, bt + 1.15, cz - 0.42), v3(0, yt - 0.25, tip[2] + 1.45)
    for sx in (1, -1):
        o = v3(sx * 0.28, 0, 0)
        beam(bone, "crane_girder_%d" % (sx > 0), t0 + o, t1 + o, 0.56, "wood_dark", width=0.26, extend=0.14)
        beam(bone, "crane_strut_%d" % (sx > 0), s0 + o, s1 + o, 0.42, "wood_dark", width=0.24, extend=0.12)
        n = 4
        for k in range(1, n):
            f = k / n
            a = s0 + (s1 - s0) * f + o
            b = v3(0, yt - 0.2, a[2] - 0.55) + o
            beam(bone, "crane_brace_%d_%d" % (sx > 0, k), a, b, 0.2, "wood_dark", width=0.2)
            add_cube(bone, "crane_bolt_%d_%d" % (sx > 0, k), b + v3(sx * 0.13, 0.05, 0), EYE, (0.06, 0.16, 0.16), "brass")
        for k, f in enumerate(np.linspace(0.08, 0.95, 6)):
            add_cube(bone, "crane_rivet_%d_%d" % (sx > 0, k), t0 + (t1 - t0) * f + o + v3(sx * 0.12, 0.0, 0), EYE, (0.04, 0.12, 0.12), "brass")
        beam(bone, "crane_end_%d" % (sx > 0), tip + o + v3(0, -0.15, 0), v3(0, yt + 0.3, tip[2]) + o, 0.22, "wood_dark", width=0.2)
    for k, f in enumerate(np.linspace(0.12, 0.9, 5)):
        add_cube(bone, "crane_rung_%d" % k, t0 + (t1 - t0) * f + v3(0, -0.18, 0), EYE, (0.72, 0.1, 0.12), "iron_band")
    beam(bone, "crane_tie", v3(0, yh + 1.1, cz + 0.2), v3(0, yt + 0.25, tip[2] + 0.2), 0.08, "chain")
    disc(bone, "crane_pulley", tip + v3(0, -0.05, 0), (1, 0, 0), 0.34, 0.26, "brass", n=3)
    # the crate on its chains (swaying)
    cb = Bone("crate_hang", origin=tuple(tip), parent=root)
    y0, y1 = gs.CRATE_Y
    for sx in (1, -1):
        beam(cb, "crate_chain_%d" % (sx > 0), tip + v3(sx * 0.1, -0.2, 0), v3(sx * 0.45, y1 + 0.05, tip[2]), 0.09, "chain")
    add_cube(cb, "crate", (0, (y0 + y1) / 2, tip[2]), EYE, (1.9, y1 - y0, 1.8), "crate", stretch=True)
    add_cube(cb, "crate_band", (0, y1 - 0.1, tip[2]), EYE, (1.95, 0.1, 1.85), "iron_band")
    return cb


def helm(bone):
    """The wheel on the bridge (brass hub and rim handles), its pedestal, the binnacle, a speaking tube."""
    hz = gs.HELM_Z
    hub = v3(0, B + 1.05, hz)
    add_cube(bone, "helm_pedestal", (0, B + 0.5, hz - 0.05), EYE, (0.4, 1.0, 0.3), {"all": "wood_dark", "+2": "brass"})
    round_bar(bone, "helm_axle", (0, hub[1], hz + 0.1), (0, hub[1], hz - 0.25), 0.1, "iron")
    wheel = Bone("helm_wheel", origin=tuple(hub), parent=bone)
    r = 0.62
    zax = v3(0, 0, 1)
    disc(wheel, "helm_hub", hub - v3(0, 0, 0.2), zax, 0.14, 0.2, "brass", n=3)
    for k in range(8):
        a = 2 * math.pi * k / 8
        dv = v3(math.cos(a), math.sin(a), 0)
        round_bar(wheel, "helm_spoke_%d" % k, hub - v3(0, 0, 0.2) + dv * 0.1, hub - v3(0, 0, 0.2) + dv * r, 0.07, "wood_mid")
        turned(wheel, "helm_handle_%d" % k, hub - v3(0, 0, 0.2) + dv * (r + 0.04), hub - v3(0, 0, 0.2) + dv * (r + 0.28),
               [(0, 0.07), (0.3, 0.1), (0.7, 0.07), (1, 0)], "brass")
    for k in range(16):
        a, a2 = 2 * math.pi * k / 16, 2 * math.pi * (k + 1) / 16
        p0, p1 = hub - v3(0, 0, 0.2) + v3(math.cos(a), math.sin(a), 0) * r, hub - v3(0, 0, 0.2) + v3(math.cos(a2), math.sin(a2), 0) * r
        beam(wheel, "helm_rim_%d" % k, p0, p1, 0.1, "wood_dark", width=0.1, up=zax, extend=0.02)
    bn = v3(1.1, B, hz + 0.2)
    disc(bone, "binnacle", bn + v3(0, 0.45, 0), (0, 1, 0), 0.24, 0.9, "wood_mid")
    disc(bone, "binnacle_top", bn + v3(0, 0.93, 0), (0, 1, 0), 0.26, 0.06, "brass")
    disc(bone, "binnacle_card", bn + v3(0, 0.97, 0), (0, 1, 0), 0.17, 0.02, {"all": "brass", "+2": "compass"})
    pipe(bone, "speaking_tube", [(-1.0, B, hz + 0.3), (-1.0, B + 1.1, hz + 0.3), (-0.75, B + 1.35, hz + 0.3)], d=0.18, flange=False)


def rudder(root):
    zr = TZ + 0.4
    piv = v3(0, 0.0, zr)
    rb = Bone("rudder", origin=tuple(piv), parent=root)
    y_top, y_bot = min(0.4, gs.keel_draw(zr) - 0.05), gs.keel_draw(zr) - 1.4
    for k, (ya, yb) in enumerate(zip(np.linspace(y_top, y_bot, 4)[:-1], np.linspace(y_top, y_bot, 4)[1:])):
        board(rb, "rudder_blade_%d" % k, v3(0.18, ya, zr), v3(0.18, ya, zr - 1.3), v3(0.18, yb, zr), v3(0.18, yb, zr - 1.4 - 0.1 * k), 0.36,
              "iron_dark", v3(1, 0, 0), overlap=1.0)
    for k, y in enumerate(np.linspace(y_top - 0.3, y_bot + 0.3, 3)):
        add_cube(rb, "rudder_strap_%d" % k, (0, y, zr - 0.7), EYE, (0.42, 0.14, 1.4), "brass")
    round_bar(rb, "rudder_stock", (0, y_bot, zr + 0.05), (0, 2.0, zr + 0.05), 0.24, "iron")


def boiler(bone, lights):
    """The boiler under the funnel: a riveted shell on a firebox whose door glows, brass bands, a steam dome,
    gauges, its uptake to the ceiling (in the engine room, lit by the room)."""
    x0, x1, y0, y1, z0, z1 = gi.BOILER
    zc = (z0 + z1) / 2
    add_cube(bone, "lit_boiler_base", (0, y0 + 0.6, zc), EYE, (x1 - x0, 1.2, z1 - z0), {"all": "boiler", "+3": "boiler_front"}, stretch=False)
    add_cube(bone, "glow_boiler_fire", (0, y0 + 0.55, z1 + 0.01), EYE, (1.4, 0.8, 0.02), "boiler_front", stretch=True)
    cylinder(bone, "lit_boiler_shell", (0, y0 + 1.2, zc), 2.2, 1.35, "boiler", n=12)
    disc(bone, "lit_boiler_top", (0, y0 + 3.42, zc), (0, 1, 0), 1.38, 0.06, "boiler", n=3)
    ring(bone, "lit_boiler_band_a", (0, y0 + 1.5, zc), 1.35, 0.08, 0.2, "brass", n=12)
    ring(bone, "lit_boiler_band_b", (0, y0 + 2.9, zc), 1.35, 0.08, 0.2, "brass", n=12)
    cylinder(bone, "lit_boiler_uptake", (0, y0 + 3.4, zc), y1 - y0 - 3.4, 0.7, "iron", n=8, tile=False)
    for k, x in enumerate((-0.55, 0.55)):
        disc(bone, "lit_boiler_gauge_%d" % k, (x, y0 + 2.2, z1 + 0.06), (0, 0, 1), 0.18, 0.06, {"all": "brass", "+2": "gauge"}, n=3)


CUSTOM_BUILDERS = dict(gc.CUSTOM_BUILDERS)
CUSTOM_BUILDERS.update(gf.BUILDERS)


# ---------------------------------------------------------------- the rooms, on the interior grid
MAX_TILE = 8
ROOM_MATERIALS = {"hold": ("hold_wall", "hold_floor", "ceil"), "engine_room": ("wall_iron", "floor_iron", "ceil"),
                  "crew": ("crew_wall", "floor", "ceil"), "cabin": ("wall_wood", "floor", "ceil")}
DEFAULT_ROOM = ("hold_wall", "floor", "ceil")


def room_at(x, y, z):
    for name, (x0, x1, y0, y1, z0, z1) in gi.ROOMS.items():
        if x0 - 0.01 <= x <= x1 + 0.01 and y0 - 0.51 <= y <= y1 + 0.01 and z0 - 0.01 <= z <= z1 + 0.01:
            return name
    return None


def surfaces(rooms_bone, g):
    """Walls, floors, ceilings, stairs of the rooms: every face between a solid cell and an open cell of a room
    (dry, door, furniture, ladder) is drawn, in the material of the room; the masts are drawn round instead."""
    k = g.k
    mast_ = np.zeros(k.shape, dtype=bool)
    for z, foot in gi.MASTS:
        mast_ |= (np.abs(g.X) < 0.5) & (np.abs(g.Z - z) < 0.5) & (g.Y > foot)
    solid = (k == gi.SOLID) & ~mast_
    opened = (k == gi.DRY) | (k >= gi.DOOR) | (k == gi.FURNITURE)
    Cl = gi.CELL
    origin = (gi.X0, gi.Y0, gi.Z0)
    mats = [DEFAULT_ROOM] + [m for m in dict.fromkeys(ROOM_MATERIALS.values()) if m != DEFAULT_ROOM]
    mat_index = np.zeros(k.shape, dtype=np.int16)
    for name, box in gi.ROOMS.items():
        mat_index[g.sel(*[b + d for b, d in zip(box, (-0.01, 0.01, -0.51, 0.01, -0.01, 0.01))])] = mats.index(ROOM_MATERIALS[name])
    count = 0
    for a in range(3):
        for s in (1, -1):
            src = [slice(None)] * 3
            dst = [slice(None)] * 3
            if s > 0:
                dst[a], src[a] = slice(0, -1), slice(1, None)
            else:
                dst[a], src[a] = slice(1, None), slice(0, -1)
            nb_open = np.zeros_like(opened)
            nb_open[tuple(dst)] = opened[tuple(src)]
            nb_mat = np.zeros_like(mat_index)
            nb_mat[tuple(dst)] = mat_index[tuple(src)]
            layer = solid & nb_open
            slot = 1 if (a == 1 and s > 0) else 2 if a == 1 else 0
            others = [b for b in range(3) if b != a]
            for idx in range(layer.shape[a]):
                sl = [slice(None)] * 3
                sl[a] = idx
                m2 = layer[tuple(sl)]
                if not m2.any():
                    continue
                plane = origin[a] + (idx + (1 if s > 0 else 0)) * Cl
                al_i = a == 1 or a == 2
                al_j = a == 1 or a == 0
                for (i0, j0, i1, j1, kk) in gc.greedy(m2, nb_mat[tuple(sl)], al_i, al_j):
                    lo, hi = [0.0] * 3, [0.0] * 3
                    b0, b1 = others
                    lo[b0], hi[b0] = origin[b0] + i0 * Cl, origin[b0] + (i1 + 1) * Cl
                    lo[b1], hi[b1] = origin[b1] + j0 * Cl, origin[b1] + (j1 + 1) * Cl
                    lo[a] = hi[a] = plane + s * 0.005
                    center = [(lo[q] + hi[q]) / 2 for q in range(3)]
                    size = [max(0.01, hi[q] - lo[q]) for q in range(3)]
                    size[a] = 0.01
                    face = ("+" if s > 0 else "-") + str(a + 1)
                    if a == 1:
                        udir, vdir = v3(1, 0, 0), v3(0, 0, 1)
                    else:
                        udir, vdir = (v3(0, 0, 1) if a == 0 else v3(1, 0, 0)), v3(0, -1, 0)
                    region = mats[kk][slot]
                    cube = add_cube(rooms_bone, "lit_%s_%d" % (region, count), center, EYE, size, {face: region}, u_dir=udir, v_dir=vdir)
                    if a == 1:
                        sub = ((i0 % MAX_TILE) / MAX_TILE, (j0 % MAX_TILE) / MAX_TILE, (i1 % MAX_TILE + 1) / MAX_TILE,
                               (j1 % MAX_TILE + 1) / MAX_TILE)
                    else:
                        hz0, hz1 = (j0, j1) if a == 0 else (i0, i1)
                        y_lo, y_hi = lo[1], hi[1]
                        room = room_at(center[0] + s * 0.3 if a == 0 else center[0], center[1],
                                       center[2] + s * 0.3 if a == 2 else center[2])
                        ry0, ry1 = (gi.ROOMS[room][2], gi.ROOMS[room][3]) if room else (y_lo, y_hi)
                        hgt = max(0.5, ry1 - ry0)
                        # (a wall below the room's floor, round a hatch, samples the bottom band of the region)
                        v0 = min(0.94, max(0.0, (ry1 - y_hi) / hgt))
                        v1 = min(1.0, max(v0 + 0.06, (ry1 - y_lo) / hgt))
                        sub = ((hz0 % MAX_TILE) / MAX_TILE, v0, (hz1 % MAX_TILE + 1) / MAX_TILE, v1)
                    for f in cube.faces.values():
                        if f is not None:
                            f["sub"] = sub
                    count += 1
    return count


def outdoor_steps(bone):
    """The steps on the open decks (forecastle stairs, steps down to the poop): drawn from the grid's step
    boxes (indoor stairs are drawn with the rooms)."""
    for name, steps in gi.STEPS.items():
        if not (name.startswith("forecastle") or name.startswith("poop")):
            continue
        for k, (x0, x1, top, za, zb) in enumerate(steps):
            base = M if name.startswith("forecastle") else P
            add_cube(bone, "step_%s_%d" % (name, k), ((x0 + x1) / 2, (base + top) / 2, (za + zb) / 2), EYE, (x1 - x0, top - base, zb - za),
                     {"all": "plate_b", "+2": "deck"})
            add_cube(bone, "step_%s_nose_%d" % (name, k), ((x0 + x1) / 2, top - 0.04, (za + zb) / 2), EYE, (x1 - x0 + 0.02, 0.08, zb - za + 0.02),
                     {"all": None, "+2": "deck", "+3": "brass", "-3": "brass"})


def beams_below(bone):
    for name, (x0, x1, y0, y1, z0, z1) in gi.ROOMS.items():
        for k, z in enumerate(np.arange(z0 + 1.0, z1 - 0.4, 2.0)):
            w = min(x1, gs.hull_x(z, y1) - 0.55) - 0.02
            xa = max(x0, -(gs.hull_x(z, y1) - 0.55)) + 0.02
            if w - xa < 0.5:
                continue
            beam(bone, "lit_beam_%s_%d" % (name, k), (xa, y1 - 0.12, z), (w, y1 - 0.12, z), 0.24, "iron_band" if name == "engine_room" else "wood_dark",
                 width=0.3)


def doors(root, g):
    anims = []
    for d, (name, box) in gi.DOORS.items():
        x0, x1, y0, y1, z0, z1 = box
        sx, sy, sz = x1 - x0, y1 - y0, z1 - z0
        thin = 0.14
        w = 0.16
        for k, at in enumerate((x0 - w / 2, x1 + w / 2)):
            add_cube(root, "lit_door_%d_jamb_%d" % (d, k), v3(at, (y0 + y1 + w) / 2, (z0 + z1) / 2), EYE, (w, sy + w, sz + 0.1), "brass")
        add_cube(root, "lit_door_%d_lintel" % d, v3((x0 + x1) / 2, y1 + w / 2, (z0 + z1) / 2), EYE, (sx + 2 * w, w, sz + 0.1), "brass")
        tracks = []
        for leaf, sgn in (("a", 1), ("b", -1)):
            xh = x1 if sgn > 0 else x0
            hinge = v3(xh, y0, (z0 + z1) / 2)
            c = v3(xh - sgn * sx / 4, (y0 + y1) / 2, (z0 + z1) / 2)
            bone = Bone("door_%d_%s" % (d, leaf), origin=tuple(hinge), parent=root)
            add_cube(bone, "lit_door_%d_%s" % (d, leaf), c, EYE, (sx / 2 - 0.02, sy, thin), {"all": "wood_dark", "+3": "door", "-3": "door"},
                     stretch=True, u_dir=v3(1, 0, 0), v_dir=v3(0, -1, 0))
            tracks.append((bone, [gg.rot_kf(0.0, (0, 0, 0)), gg.rot_kf(1.0, (0, sgn * 100, 0))]))
        anims.append(gg.animation("door_%d" % d, 1.0, "hold", tracks))
    return anims


def fallbacks(root):
    for i, b in enumerate(gd.BLOCKS):
        x0, x1, y0, y1, z0, z1 = gd.footprint(b["block"], b["x"], b["y"], b["z"], b["yaw"], b["scale"])
        bone = Bone("fallback_%d" % i, parent=root)
        region = gd.FALLBACK_REGION.get(b["block"], "wood_mid")
        if region == "lantern":
            add_cube(bone, "lit_fallback_%d" % i, v3((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), EYE, (0.3, 0.42, 0.3),
                     {"all": "lantern", "+2": "iron", "-2": "iron"}, stretch=True)
            continue
        add_cube(bone, "lit_fallback_%d" % i, v3((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), EYE,
                 (max(0.04, x1 - x0), max(0.04, y1 - y0), max(0.04, z1 - z0)), region)


# ---------------------------------------------------------------- the model
def build(g):
    root = Bone("gear_steamship")
    hull_bone = Bone("hull", parent=root)
    upper = Bone("upperworks", parent=root)
    deck_bone = Bone("deck", parent=root)
    bow_bone = Bone("bow", parent=root)
    ropes = Bone("ropes", parent=root)
    lights = Bone("lanterns", parent=root)
    detail = Bone("detail", parent=root)
    rooms = Bone("rooms", parent=root)
    fittings = Bone("fittings", parent=root)
    furniture = Bone("furniture", parent=root)
    n = hull(hull_bone)
    boom_tip = stem(bow_bone)
    stern(hull_bone, lights)
    trims(hull_bone, detail)
    bulwarks(hull_bone, detail)
    decks(deck_bone)
    deckhouse(upper, lights)
    engine_house(upper, lights, fittings)
    masts = {name: mast(root, fittings, name) for name in MASTS}
    sails_info = []
    yards = sails(root, masts, sails_info)
    rigging(ropes, yards)
    crane(upper, root)
    helm(upper)
    rudder(root)
    outdoor_steps(deck_bone)
    # the bow lantern hanging from the boom on its chain, the forecastle's lanterns on their posts
    lantern(lights, "lantern_bow", boom_tip - v3(0, 0.3, 0.4), drop=1.0, s=2.4)
    for side, sn in SIDES:
        x = side * (gs.hull_x(16.4, F) - 0.3)
        add_cube(bow_bone, "fc_lamp_post_" + sn, (x, gs.FORECASTLE_CAP_Y + 1.5, 16.4), EYE, (0.18, 0.6, 0.18), "wood_dark")
        lantern(lights, "lantern_fc_" + sn, v3(x, gs.FORECASTLE_CAP_Y + 1.8, 16.4), hang=False, s=1.3)
        x = side * (gi.GALLERY[1] + 0.25)
        add_cube(upper, "poop_lamp_post_" + sn, (x, gs.POOP_CAP_Y + 1.4, TZ - 1.0), EYE, (0.18, 0.6, 0.18), "wood_dark")
        lantern(lights, "lantern_poop_" + sn, v3(x, gs.POOP_CAP_Y + 1.7, TZ - 1.0), hang=False, s=1.3)
    # the rooms, their doors, the beams, the boiler, the furniture
    m = surfaces(rooms, g)
    beams_below(fittings)
    boiler(furniture, lights)
    for builder, kwargs, solid in gd.CUSTOM:
        CUSTOM_BUILDERS[builder](furniture, **kwargs)
    fallbacks(root)
    return root, n, m, sails_info


def build_animations(root, sails_info):
    kf, rot_kf, animation, find = gg.kf, gg.rot_kf, gg.animation, gg.find
    anims = []
    tracks = []
    for k, (b, side_billow) in enumerate(sails_info):
        ph = 0.37 * k
        sc = [kf("scale", t, (1, 1, s), "catmullrom") for t, s in ((0, 1.0), (0.9 + ph * 0.1, 1.1), (1.8, 0.93), (2.7, 1.06), (3.6, 1.0))]
        rt = [rot_kf(t, (a, 0, 0), "catmullrom") for t, a in ((0, 0), (1.2, -1.0), (2.4, 0.6), (3.6, 0))]
        tracks.append((b, sc + rt))
    anims.append(animation("sail_wind", 3.6, "loop", tracks))
    tracks = [(b, [kf("scale", 0.0, (1, 1, 1)), kf("scale", 1.0, (FURL_SCALE.get(b.name, 0.95), 0, 0))]) for b, _ in sails_info]
    anims.append(animation("sail_furl", 1.0, "hold", tracks))
    wheel, rud = find(root, "helm_wheel"), find(root, "rudder")
    anims.append(animation("steer", 2.0, "hold", [
        (wheel, [rot_kf(0.0, (0, 0, -150)), rot_kf(1.0, (0, 0, 0)), rot_kf(2.0, (0, 0, 150))]),
        (rud, [rot_kf(0.0, (0, -28, 0)), rot_kf(1.0, (0, 0, 0)), rot_kf(2.0, (0, 28, 0))])]))

    def loop_kfs(fn, period, n=8):
        return [rot_kf(round(period * i / n, 4), fn(period * i / n), "catmullrom") for i in range(n + 1)]

    def bones(b, pred):
        out = [b] if pred(b) else []
        for c in b.children:
            out += bones(c, pred)
        return out
    tracks = []
    for k, b in enumerate(bones(root, lambda b: (b.name.startswith("lantern_") and b.name != "lanterns") or b.name == "crate_hang")):
        a = 3 if b.name == "crate_hang" else 5
        w, ph = 2 * math.pi / 2.4, 0.35 * k
        tracks.append((b, loop_kfs(lambda t, ph=ph, a=a: (a * math.cos(w * (t - ph)), 0, a * 0.6 * math.sin(w * (t - ph))), 2.4)))
    anims.append(animation("lantern_sway", 2.4, "loop", tracks))
    # the gear wheels turn with the speed (the mod plays "engine" on the distance run, looping every 4 units:
    # a quarter turn per second at the normal speed); neighbours turn the other way
    tracks = []
    period = 4.0
    for b in bones(root, lambda b: b.name.startswith("gear_") and b is not root):
        if b.name == "gear_flywheel":
            # the engine room's flywheel and crankshaft: whole turns a loop (the pistons follow its cranks)
            spd = 360.0 * gf.FLYWHEEL_TURNS / period
            tracks.append((b, [rot_kf(round(period * i / 8, 4), (spd * period * i / 8, 0, 0)) for i in range(9)]))
            continue
        sgn = -1 if any(t in b.name for t in ("_b_", "gear_bow", "gear_gallery")) else 1
        n_teeth = 12 if "big" in b.name else 9
        spd = sgn * 360.0 * (12.0 / n_teeth) / period * (0.5 if "big" in b.name else 1.0)
        tracks.append((b, [rot_kf(round(period * i / 4, 4), (spd * period * i / 4, 0, 0)) for i in range(5)]))
    # the pistons ride on the cranks (half a turn apart): their height follows the cosine of the flywheel's angle
    n = 8 * gf.FLYWHEEL_TURNS
    for b in bones(root, lambda b: b.name.startswith("piston_")):
        ph = math.pi * int(b.name.split("_")[1])
        keys = [kf("position", round(period * i / n, 4), (0, 16 * gf.PISTON_STROKE * (math.cos(2 * math.pi * gf.FLYWHEEL_TURNS * i / n + ph) - 1), 0),
                   "catmullrom") for i in range(n + 1)]
        tracks.append((b, keys))
    anims.append(animation("engine", period, "loop", tracks))
    return anims


def main():
    g = gi.build()
    gd.build()
    gd.apply_to_grid(g)
    gd.write(os.path.join(ROOT, gd.DECOR_PATH))
    size = g.write(os.path.join(ROOT, gi.GRID_PATH))
    reached, total = gi.walkable_report(g)
    print("decor blocks:", len(gd.BLOCKS), "seats:", len(gd.SEATS), "standing places:", total,
          "unreachable places:", [k for k, v in reached.items() if not v])
    root, n, m, sails_info = build(g)
    anims = build_animations(root, sails_info)
    anims += doors(gg.find(root, "rooms"), g)
    tex_dir = os.path.join(ROOT, "src/main/resources/assets/medievalships/textures")
    paths = [os.path.join(tex_dir, "entity/gear_steamship.png"), os.path.join(tex_dir, "entity/gear_steamship_sails.png")]
    gt.make_texture(paths[0])
    gt.make_sail_texture(paths[1])
    gt.make_item_icon(os.path.join(tex_dir, "item/gear_steamship.png"))
    textures = []
    for k, (p, size_) in enumerate(zip(paths, (gt.SIZE, gt.SAIL_SIZE))):
        with open(p, "rb") as f:
            png = f.read()
        t = gn.texture_entry(os.path.basename(p), size_, png, "entity", "gear_steamship.png")
        t["id"] = str(k)
        textures.append(t)
    model = gn.export(root, anims, textures, [
        os.path.join(ROOT, "blockbench/gear_steamship.bbmodel"),
        os.path.join(ROOT, "src/main/resources/assets/medievalships/models/entity/gear_steamship.bbmodel"),
    ], name="gear_steamship", visible_box=(56, 40, 0))
    print("grid bytes:", size, "hull boards:", n, "grid surfaces:", m, "cubes:", len(model["elements"]),
          "animations:", [a["name"] for a in model["animations"]])
    # the Python reference of the model for the Java loader test (NewShipModelsTest)
    import subprocess
    subprocess.run([sys.executable, os.path.join(ROOT, "tools/reference_quads.py"),
                    os.path.join(ROOT, "src/main/resources/assets/medievalships/models/entity/gear_steamship.bbmodel"),
                    os.path.join(ROOT, "src/test/resources/gear_steamship_reference_quads.json"),
                    "sail_furl=0.3,steer=1.3,lantern_sway=0.6,engine=1.0,sail_wind=0.0,door_0=0.6"], check=True)


if __name__ == "__main__":
    main()
