#!/usr/bin/env python3
"""Generates the medieval galley Blockbench model (.bbmodel), its texture and
its animations.

Usage:  python3 tools/generate_galley.py

Outputs:
  blockbench/galley.bbmodel                                   (editable in Blockbench, texture embedded)
  src/main/resources/assets/medievalships/models/entity/galley.bbmodel  (loaded by the mod)
  src/main/resources/assets/medievalships/textures/entity/galley.png

The mod loads the .bbmodel directly, so the model can be edited in Blockbench
and dropped back into a resource pack: bone names listed in docs/MODELE.md must
be kept for the animations to work.

Conventions (shared with fr.medievalships.client.model.BbModel):
  * ship-local blocks: +x port, +y up, +z bow; Blockbench pixels: (-16x, 16y, -16z)
    so the bow points to Blockbench "north" (-Z).
  * rotations are Blockbench/three.js ZYX Euler angles: R = Rz * Ry * Rx.
  * group (bone) origins and cube coordinates are absolute, unrotated.
  * animation keyframes are added to the bone as in the Blockbench viewer: rotation
    (kx, ky, kz) degrees are added to the bone Euler, position adds pixels, scale multiplies.
"""
import base64
import io
import json
import math
import os
import sys
import uuid
import zlib

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import hull_profile as hp  # noqa: E402
import ship_details as sd  # noqa: E402
from galley_texture import REGIONS, SIZE, make_texture  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_uuid_counter = [0]


def new_uuid():
    _uuid_counter[0] += 1
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "medievalships/galley/%d" % _uuid_counter[0]))


# ---------------------------------------------------------------- math
M = np.diag([-1.0, 1.0, -1.0])  # local blocks -> blockbench axes (without the x16)


def v3(*a):
    return np.array(a, dtype=float)


def norm(v):
    n = np.linalg.norm(v)
    return v / n if n > 1e-9 else v


def rx(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def ry(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def rz(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def euler_zyx_matrix(deg):
    a, b, c = [math.radians(d) for d in deg]
    return rz(c) @ ry(b) @ rx(a)


def matrix_to_euler_zyx(R):
    sb = max(-1.0, min(1.0, -R[2, 0]))
    b = math.asin(sb)
    if abs(math.cos(b)) > 1e-6:
        a = math.atan2(R[2, 1], R[2, 2])
        c = math.atan2(R[1, 0], R[0, 0])
    else:  # gimbal lock
        a = math.atan2(-R[1, 2], R[1, 1])
        c = 0.0
    return [round(math.degrees(x), 4) for x in (a, b, c)]


def to_bb_point(p):
    return [round(-p[0] * 16, 4), round(p[1] * 16, 4), round(-p[2] * 16, 4)]


def to_bb_rot(R):
    return M @ R @ M


# Blockbench / Minecraft face conventions in cube space:
# face -> (normal, u direction, v direction)
FACE_AXES = {
    "north": (v3(0, 0, -1), v3(-1, 0, 0), v3(0, -1, 0)),
    "south": (v3(0, 0, 1), v3(1, 0, 0), v3(0, -1, 0)),
    "west": (v3(-1, 0, 0), v3(0, 0, 1), v3(0, -1, 0)),
    "east": (v3(1, 0, 0), v3(0, 0, -1), v3(0, -1, 0)),
    "up": (v3(0, 1, 0), v3(1, 0, 0), v3(0, 0, 1)),
    "down": (v3(0, -1, 0), v3(1, 0, 0), v3(0, 0, -1)),
}
# local cube axis sign -> blockbench face (see module doc: bb x = -M col1, bb y = M col2, bb z = -M col3)
SEMANTIC_FACE = {"+1": "west", "-1": "east", "+2": "up", "-2": "down", "+3": "north", "-3": "south"}


# ---------------------------------------------------------------- model structures
class Bone:
    def __init__(self, name, origin=(0, 0, 0), rot=None, parent=None):
        self.name = name
        self.origin = v3(*origin)
        self.rot = np.eye(3) if rot is None else rot  # local-space rotation
        self.parent = parent
        self.children = []
        self.cubes = []
        self.uuid = new_uuid()
        if parent:
            parent.children.append(self)

    def chain(self):
        b, out = self, []
        while b:
            out.append(b)
            b = b.parent
        return out  # innermost first

    def to_world(self, p):
        for b in self.chain():
            p = b.rot @ (p - b.origin) + b.origin
        return p

    def to_frame(self, p):
        for b in reversed(self.chain()):
            p = b.rot.T @ (p - b.origin) + b.origin
        return p

    def frame_rot(self):
        R = np.eye(3)
        for b in self.chain():
            R = b.rot @ R
        return R


class Cube:
    def __init__(self, bone, name, center, axes, size, faces):
        self.bone, self.name = bone, name
        self.center, self.axes, self.size = center, axes, size
        self.faces = faces  # bb face name -> dict(region, u_dir, v_dir, stretch) or None
        self.uuid = new_uuid()
        bone.cubes.append(self)


def add_cube(bone, name, center, axes, size, regions, world=True, stretch=False,
             u_dir=None, v_dir=None, density=1.0):
    """center/axes in world (ship-local) space unless world=False (bone frame).
    regions: str (all faces) or dict with keys among '+1','-1','+2','-2','+3','-3','all'.
    u_dir/v_dir: optional world-space hints for texture orientation."""
    axes = np.array(axes, dtype=float)
    center = v3(*center)
    if world:
        center = bone.to_frame(center)
        axes = bone.frame_rot().T @ axes
        if u_dir is not None:
            u_dir = bone.frame_rot().T @ np.asarray(u_dir, dtype=float)
        if v_dir is not None:
            v_dir = bone.frame_rot().T @ np.asarray(v_dir, dtype=float)
    if isinstance(regions, str):
        regions = {"all": regions}
    faces = {}
    for sem, bbface in SEMANTIC_FACE.items():
        reg = regions.get(sem, regions.get("all"))
        faces[bbface] = None if reg is None else {
            "region": reg, "u_dir": u_dir, "v_dir": v_dir, "stretch": stretch, "density": density}
    return Cube(bone, name, center, axes, np.array(size, dtype=float), faces)


def frame_from(u, up_hint):
    u = norm(u)
    v = up_hint - np.dot(up_hint, u) * u
    if np.linalg.norm(v) < 1e-6:
        v = v3(0, 0, 1) - np.dot(v3(0, 0, 1), u) * u
    v = norm(v)
    n = np.cross(u, v)
    return np.column_stack([u, v, n])


def beam(bone, name, p0, p1, th, region, width=None, up=v3(0, 1, 0), extend=0.0, **kw):
    p0, p1 = v3(*p0), v3(*p1)
    d = p1 - p0
    L = np.linalg.norm(d) + 2 * extend
    if abs(np.dot(norm(d), up)) > 0.98:
        up = v3(1, 0, 0)
    axes = frame_from(d, up)
    return add_cube(bone, name, (p0 + p1) / 2, axes, (L, th, width if width else th), region, **kw)


def board(bone, name, a0, a1, b0, b1, th, region, outward, overlap=1.06, inner=None):
    """Plank between two cross sections: a0/a1 = lower/upper edge at station A, b0/b1 at B."""
    a0, a1, b0, b1 = map(np.asarray, (a0, a1, b0, b1))
    c = (a0 + a1 + b0 + b1) / 4
    u = ((b0 + b1) - (a0 + a1)) / 2
    L = np.linalg.norm(u)
    u = u / L
    vp = ((a1 - a0) + (b1 - b0)) / 2
    W = np.linalg.norm(vp)
    v = norm(vp - np.dot(vp, u) * u)
    n = np.cross(u, v)
    if np.dot(n, outward) < 0:
        u, n = -u, -n
    c = c - n * th / 2
    regions = {"all": region}
    if inner:
        regions["-3"] = inner
    return add_cube(bone, name, c, np.column_stack([u, v, n]), (L * overlap + 0.04, W * 1.03 + 0.02, th), regions)


# ---------------------------------------------------------------- the galley
STATIONS = [-10.0, -9.3, -8.4, -7.3, -6.0, -4.4, -2.6, -0.9, 0.9, 2.6, 4.4, 6.0, 7.3, 8.4, 9.3, 10.0]
OAR_Z = [-5.6 + i * 1.6 for i in range(8)]
BENCH_Z = [-4.8, -1.6, 1.6, 4.8]
MAST_Z = 0.5
MAST_TOP = 13.2
YARD_A = v3(0.25, 14.6, -4.6)   # upper (aft) end of the lateen yard
YARD_B = v3(0.25, 3.7, 8.2)     # lower (fore) end


def section(z, side):
    """Cross-section points (x, y) on one side (side=+1 port, -1 starboard)."""
    w, yk, yr = hp.half_width(z), hp.keel_y(z), hp.rail_y(z)
    pts = [
        (0.10, yk),
        (0.62 * w, yk * 0.82),
        (0.93 * w, yk * 0.25),
        (1.00 * w, yr - 0.95),
        (1.01 * w, yr - 0.50),
        (1.02 * w, yr),
    ]
    return [v3(side * max(x, 0.1), y, z) for x, y in pts]


STRAKE_REGIONS = ["hull_dark", "hull_dark", "hull_mid", "red", "hull_light"]


def build():
    root = Bone("galley")
    hull = Bone("hull", parent=root)
    deck = Bone("deck", parent=root)
    stern = Bone("stern", parent=root)
    bow = Bone("bow", parent=root)
    mast = Bone("mast", origin=(0, 0.45, MAST_Z), parent=root)
    ropes = Bone("ropes", parent=root)
    lanterns = Bone("lanterns", parent=root)

    # ---- hull planking
    for side in (1, -1):
        sname = "p" if side > 0 else "s"
        for i in range(len(STATIONS) - 1):
            za, zb = STATIONS[i], STATIONS[i + 1]
            A, B = section(za, side), section(zb, side)
            for k, reg in enumerate(STRAKE_REGIONS):
                mid = (A[k] + A[k + 1] + B[k] + B[k + 1]) / 4
                outward = norm(v3(side, -0.6 if k < 2 else 0.0, 0) + v3(0, 0, 0.3 * np.sign(mid[2])))
                board(hull, "hull_%s%d_%d" % (sname, i, k), A[k], A[k + 1], B[k], B[k + 1], 0.1, reg,
                      outward, inner="hull_mid" if k >= 2 else None)
            # rail cap
            pa = v3(side * hp.half_width(za) * 1.02, hp.rail_y(za) + 0.06, za)
            pb = v3(side * hp.half_width(zb) * 1.02, hp.rail_y(zb) + 0.06, zb)
            beam(hull, "rail_%s%d" % (sname, i), pa, pb, 0.12, "rail", width=0.28, extend=0.08)
    # keel
    for i in range(len(STATIONS) - 1):
        za, zb = STATIONS[i], STATIONS[i + 1]
        beam(hull, "keel_%d" % i, (0, hp.keel_y(za) - 0.05, za), (0, hp.keel_y(zb) - 0.05, zb), 0.22,
             "dark_wood", width=0.3, extend=0.06)

    # ---- stem (bow) and stern posts, curving upwards
    def post(bone, name, sign, top_y, reach, region="hull_light"):
        z0 = sign * 10.0
        pts = [v3(0, hp.keel_y(z0) - 0.1, z0)]
        n = 6
        for j in range(1, n + 1):
            t = j / n
            pts.append(v3(0, hp.keel_y(z0) + (top_y - hp.keel_y(z0)) * t,
                          z0 + sign * reach * (t ** 2.2)))
        for j in range(len(pts) - 1):
            beam(bone, "%s_%d" % (name, j), pts[j], pts[j + 1], 0.42, region, width=0.62, extend=0.12)
        return pts[-1]

    stem_top = post(bow, "stem", 1, 3.9, 1.0)
    stern_top = post(stern, "sternpost", -1, 3.7, 0.95)
    # carved bow head
    add_cube(bow, "figurehead", stem_top + v3(0, 0.25, 0.12), np.eye(3), (0.55, 0.5, 0.7), "gold")
    add_cube(bow, "figurehead_top", stem_top + v3(0, 0.6, 0.0), np.eye(3), (0.35, 0.3, 0.45), "hull_light")
    # stern scroll
    add_cube(stern, "stern_scroll", stern_top + v3(0, 0.3, 0.15), np.eye(3), (0.5, 0.5, 0.55), "hull_light")
    add_cube(stern, "stern_scroll_cap", stern_top + v3(0, 0.62, 0.3), np.eye(3), (0.36, 0.25, 0.4), "gold")

    # ---- decks (two half slabs per piece so the plan follows the taper)
    def deck_span(z0, z1, n, y, tag):
        for j in range(n):
            za = z0 + (z1 - z0) * j / n
            zb = z0 + (z1 - z0) * (j + 1) / n
            wa, wb = hp.inner_half_width(za), hp.inner_half_width(zb)
            wmax = max(wa, wb)
            for side in (1, -1):
                ea, eb = v3(side * (wa + 0.08), 0, za), v3(side * (wb + 0.08), 0, zb)
                u = norm(eb - ea)
                inward = norm(np.cross(u, v3(0, 1, 0))) * 1.0
                if np.dot(inward, v3(-side, 0, 0)) < 0:
                    inward = -inward
                width = wmax * 1.08 + 0.2
                top = y - (0.006 if side < 0 else 0.0)
                c = (ea + eb) / 2 + inward * width / 2 + v3(0, top - 0.075, 0)
                axes = np.column_stack([u, v3(0, 1, 0), np.cross(u, v3(0, 1, 0))])
                L = np.linalg.norm(eb - ea) + 0.04
                add_cube(deck, "deck_%s%d_%s" % (tag, j, "p" if side > 0 else "s"), c, axes,
                         (L, 0.15, width), {"all": "deck", "-2": "dark_wood"})

    deck_span(-9.7, hp.AFT_DECK_START, 3, hp.RAISED_DECK_Y, "aft")
    deck_span(hp.AFT_DECK_START, hp.FORE_DECK_START, 9, hp.MAIN_DECK_Y, "main")
    deck_span(hp.FORE_DECK_START, 9.6, 3, hp.RAISED_DECK_Y, "fore")
    for zz, tag in ((hp.AFT_DECK_START, "aft"), (hp.FORE_DECK_START, "fore")):
        w = hp.inner_half_width(zz)
        add_cube(deck, "riser_" + tag, (0, (hp.MAIN_DECK_Y + hp.RAISED_DECK_Y) / 2, zz), np.eye(3),
                 (2 * w + 0.1, hp.RAISED_DECK_Y - hp.MAIN_DECK_Y, 0.12), "dark_wood")

    # rowing benches (also the passenger seats)
    for k, bz in enumerate(BENCH_Z):
        w = hp.inner_half_width(bz)
        add_cube(deck, "bench_%d" % k, (0, hp.MAIN_DECK_Y + 0.42, bz), np.eye(3), (2 * w - 0.05, 0.1, 0.42),
                 {"all": "hull_light", "+2": "rail"})
        for sx in (-0.9, 0.9):
            add_cube(deck, "bench_leg_%d_%s" % (k, "p" if sx > 0 else "s"), (sx, hp.MAIN_DECK_Y + 0.19, bz),
                     np.eye(3), (0.14, 0.38, 0.14), "dark_wood")
    # a few barrels and crates for life
    add_cube(deck, "crate_1", (1.2, hp.MAIN_DECK_Y + 0.3, 6.4), np.eye(3), (0.6, 0.6, 0.6), {"all": "dark_wood", "+2": "end_grain"})
    add_cube(deck, "crate_2", (1.15, hp.MAIN_DECK_Y + 0.85, 6.35), np.eye(3), (0.45, 0.5, 0.45), {"all": "hull_mid", "+2": "end_grain"})
    add_cube(deck, "barrel", (-1.3, hp.MAIN_DECK_Y + 0.35, 6.2), ry(0.4), (0.55, 0.7, 0.55), {"all": "hull_mid", "+2": "end_grain", "-2": "end_grain"})
    # deck details: amphorae, rope coils, a bucket, the pin rail around the mast foot
    me = sys.modules[__name__]
    for k, (x, z) in enumerate(((-1.25, 7.0), (-1.0, 6.75), (1.3, -5.6), (1.05, -5.85))):
        sd.amphora(me, deck, "amphora_%d" % k, (x, hp.MAIN_DECK_Y, z), clay="hull_light", dark="dark_wood")
    sd.rope_coil(me, deck, "coil_fore", (-0.9, hp.MAIN_DECK_Y, 3.2), r=0.3)
    sd.rope_coil(me, deck, "coil_aft", (0.95, hp.MAIN_DECK_Y, -3.2), r=0.3)
    sd.bucket(me, deck, "bucket", (-1.2, hp.MAIN_DECK_Y, -5.7))
    sd.fife_rail(me, deck, "fife", 0.0, MAST_Z, hp.MAIN_DECK_Y, half=0.55)
    # bronze ram at the waterline and the bow anchor with its cable
    beam(bow, "ram", (0, 0.05, 9.6), (0, 0.15, 11.9), 0.34, "gold", width=0.4, extend=0.05)
    beam(bow, "ram_tip", (0, 0.15, 11.6), (0, 0.18, 12.3), 0.22, "gold", width=0.26)
    for side in (1,):
        ax, az = side * (hp.half_width(8.4) + 0.12), 8.4
        beam(bow, "anchor_shank", (ax, hp.rail_y(8.4) - 0.1, az), (ax, 0.2, az - 0.05), 0.12, "iron")
        beam(bow, "anchor_arm_a", (ax, 0.2, az - 0.05), (ax, 0.55, az - 0.45), 0.1, "iron")
        beam(bow, "anchor_arm_b", (ax, 0.2, az - 0.05), (ax, 0.55, az + 0.35), 0.1, "iron")
        beam(bow, "anchor_stock", (ax, hp.rail_y(8.4) - 0.2, az - 0.35), (ax, hp.rail_y(8.4) - 0.2, az + 0.35), 0.08, "dark_wood")
        beam(bow, "anchor_cable", (ax, hp.rail_y(8.4) + 0.05, az), (0.5, hp.rail_y(8.4) - 0.05, 9.2), 0.07, "rope")

    # ---- stern castle: posts, red canopy, railings, helm seat
    zf, zb_ = -6.8, -9.25
    wf, wb = hp.inner_half_width(zf) - 0.1, hp.inner_half_width(zb_) - 0.05
    posts = [v3(wf, 0, zf), v3(-wf, 0, zf), v3(wb, 0, zb_), v3(-wb, 0, zb_)]
    roof_y = 3.25
    for k, p in enumerate(posts):
        beam(stern, "cabin_post_%d" % k, (p[0], hp.RAISED_DECK_Y, p[2]), (p[0], roof_y, p[2]), 0.16, "dark_wood")
    # side beams under the canopy
    for side in (1, -1):
        beam(stern, "cabin_beam_%s" % ("p" if side > 0 else "s"), (side * wf, roof_y, zf), (side * wb, roof_y, zb_),
             0.14, "dark_wood", extend=0.1)
    beam(stern, "cabin_beam_front", (-wf, roof_y, zf), (wf, roof_y, zf), 0.14, "dark_wood", extend=0.1)
    beam(stern, "cabin_beam_back", (-wb, roof_y, zb_), (wb, roof_y, zb_), 0.14, "dark_wood", extend=0.1)
    # canopy: two sloped cloth panels meeting at a ridge
    ridge_y = roof_y + 0.65
    for side in (1, -1):
        eave_f = v3(side * (wf + 0.45), roof_y - 0.1, zf + 0.35)
        eave_b = v3(side * (wb + 0.45), roof_y - 0.1, zb_ - 0.3)
        ridge_f = v3(0, ridge_y, zf + 0.35)
        ridge_b = v3(0, ridge_y, zb_ - 0.3)
        board(stern, "canopy_%s" % ("p" if side > 0 else "s"), eave_b, ridge_b, eave_f, ridge_f, 0.08,
              "canopy", v3(side * 0.4, 1, 0), overlap=1.0)
        # valance hanging along the eave
        mid = (eave_f + eave_b) / 2 + v3(0, -0.22, 0)
        u = norm(eave_f - eave_b)
        axes = np.column_stack([u, v3(0, 1, 0), np.cross(u, v3(0, 1, 0))])
        add_cube(stern, "valance_%s" % ("p" if side > 0 else "s"), mid, axes,
                 (np.linalg.norm(eave_f - eave_b) + 0.5, 0.45, 0.03),
                 {"all": "valance", "+1": None, "-1": None, "+2": None, "-2": None}, stretch=True,
                 v_dir=v3(0, -1, 0))
    add_cube(stern, "valance_front", v3(0, roof_y - 0.32, zf + 0.35), np.eye(3), (2 * wf + 0.9, 0.45, 0.03),
             {"all": None, "+3": "valance", "-3": "valance"}, stretch=True, v_dir=v3(0, -1, 0))
    # railing (barriere) at the front of the stern deck, gap in the middle
    for side in (1, -1):
        x0, x1 = side * 0.55, side * (hp.inner_half_width(hp.AFT_DECK_START) - 0.05)
        zr = hp.AFT_DECK_START - 0.1
        beam(stern, "rail_front_%s" % ("p" if side > 0 else "s"), (x0, hp.RAISED_DECK_Y + 0.75, zr),
             (x1, hp.RAISED_DECK_Y + 0.75, zr), 0.1, "rail", width=0.14, extend=0.05)
        for j, x in enumerate(np.linspace(x0, x1, 4)):
            beam(stern, "baluster_%s%d" % ("p" if side > 0 else "s", j), (x, hp.RAISED_DECK_Y, zr),
                 (x, hp.RAISED_DECK_Y + 0.75, zr), 0.1, "dark_wood")
    # helmsman stool
    add_cube(stern, "helm_seat", (0, hp.RAISED_DECK_Y + 0.22, -8.05), np.eye(3), (0.5, 0.12, 0.45), "rail")
    add_cube(stern, "helm_seat_leg", (0, hp.RAISED_DECK_Y + 0.08, -8.05), np.eye(3), (0.18, 0.18, 0.18), "dark_wood")
    # under the canopy: carpet, cushions, the captain's chest with a chart, a small water jar
    yr = hp.RAISED_DECK_Y
    sd.rug(me, stern, "cabin_rug", (0, yr, -8.0), 1.7, 2.0)
    for side in (1, -1):
        sn = "p" if side > 0 else "s"
        add_cube(stern, "cushion_" + sn, (side * 0.85, yr + 0.08, -7.45), ry(0.15 * side), (0.5, 0.14, 0.5), "red")
        add_cube(stern, "cushion_top_" + sn, (side * 0.85, yr + 0.16, -7.45), ry(0.15 * side), (0.38, 0.04, 0.38), "gold")
    add_cube(stern, "captain_chest", (-0.85, yr + 0.22, -8.85), np.eye(3), (0.6, 0.44, 0.42), {"all": "dark_wood", "+2": "hull_mid"})
    add_cube(stern, "captain_chest_band", (-0.85, yr + 0.3, -8.85), np.eye(3), (0.63, 0.06, 0.45), {"all": "iron", "+2": None, "-2": None})
    add_cube(stern, "captain_chart", (-0.85, yr + 0.45, -8.85), ry(0.2), (0.44, 0.012, 0.34), {"all": None, "+2": "chart"}, stretch=True)
    sd.amphora(me, stern, "cabin_jar", (0.85, yr, -8.85), clay="hull_light", dark="dark_wood")

    # ---- steering oars (one on each quarter), animated by "steer"
    for side in (1, -1):
        sname = "p" if side > 0 else "s"
        zp = -8.4
        pivot = v3(side * (hp.half_width(zp) + 0.12), hp.rail_y(zp) - 0.15, zp)
        rb = Bone("rudder_" + sname, origin=pivot, parent=root)
        blade_top = pivot + v3(side * 0.25, -2.2, -1.5)
        blade_bot = pivot + v3(side * 0.32, -3.4, -2.3)
        beam(rb, "rudder_shaft_" + sname, pivot + v3(0, 0.25, 0.15), blade_top, 0.16, "oar", extend=0.05)
        beam(rb, "rudder_blade_" + sname, blade_top, blade_bot, 0.08, "hull_mid", width=0.62, up=v3(1, 0, 0))
        # tiller bar towards the helmsman
        tip = v3(side * 0.35, hp.RAISED_DECK_Y + 0.85, -7.65)
        beam(rb, "tiller_" + sname, pivot + v3(0, 0.1, 0), tip, 0.1, "dark_wood")
        add_cube(rb, "rudder_lashing_" + sname, pivot, np.eye(3), (0.26, 0.26, 0.26), "iron")

    # ---- mast, yard, sail, flag
    beam(mast, "mast", (0, hp.MAIN_DECK_Y - 0.2, MAST_Z), (0, MAST_TOP, MAST_Z), 0.38, "mast")
    add_cube(mast, "mast_step", (0, hp.MAIN_DECK_Y + 0.12, MAST_Z), np.eye(3), (0.7, 0.25, 0.7), "dark_wood")
    add_cube(mast, "mast_cap", (0, MAST_TOP - 0.1, MAST_Z), np.eye(3), (0.55, 0.3, 0.55), "dark_wood")
    beam(mast, "flagpole", (0, MAST_TOP, MAST_Z), (0, MAST_TOP + 1.2, MAST_Z), 0.1, "dark_wood")

    flag_root = v3(0, MAST_TOP + 1.1, MAST_Z)
    flag = Bone("flag", origin=flag_root, parent=mast)
    add_cube(flag, "flag_a", flag_root + v3(0, -0.28, -0.45), np.eye(3), (0.03, 0.55, 0.9),
             {"all": None, "+1": "flag", "-1": "flag"}, stretch=True)
    tip_root = flag_root + v3(0, 0, -0.9)
    flag_tip = Bone("flag_tip", origin=tip_root, parent=flag)
    add_cube(flag_tip, "flag_b", tip_root + v3(0, -0.24, -0.4), np.eye(3), (0.03, 0.4, 0.8),
             {"all": None, "+1": "flag", "-1": "flag"}, stretch=True)

    # yard: bone rotated so the spar lies along the bone's local +z axis
    d = YARD_B - YARD_A
    theta = math.atan2(-d[1], d[2])  # rotation about +x taking +z onto d
    t_cross = (MAST_Z - YARD_A[2]) / d[2]
    yard_origin = YARD_A + d * t_cross
    yard = Bone("yard", origin=yard_origin, rot=rx(theta), parent=mast)
    yard_len = np.linalg.norm(d)
    tA = np.linalg.norm(yard_origin - YARD_A)
    O = yard_origin
    za, zb = O[2] - tA, O[2] - tA + yard_len
    add_cube(yard, "yard_spar_upper", (O[0], O[1], (za + O[2]) / 2 - 0.2), np.eye(3),
             (0.2, 0.2, (O[2] - za) + 0.6), "mast", world=False)
    add_cube(yard, "yard_spar_lower", (O[0] + 0.02, O[1] - 0.02, (zb + O[2]) / 2 + 0.2), np.eye(3),
             (0.18, 0.18, (zb - O[2]) + 0.6), "mast", world=False)
    add_cube(yard, "yard_lashing", (O[0], O[1], O[2]), np.eye(3), (0.3, 0.3, 0.5), "rope", world=False)

    sail_h = 8.6
    sail_mid = v3(O[0] - 0.08, O[1], (za + zb) / 2)
    sail = Bone("sail", origin=sail_mid, parent=yard)
    # billowed sail: a grid of tilted panels following the bellied cloth (in the yard frame:
    # z along the yard, y down the sail, the belly towards -x); each panel maps its own part of
    # the triangular sail texture, so the cloth stays continuous
    nx, ny, depth = 7, 6, 0.75

    def cloth(fu, fy):
        belly = depth * math.sin(math.pi * fu) ** 0.7 * math.sin(math.pi * min(1.0, fy * 0.7))
        return v3(O[0] - 0.08 - belly, O[1] - 0.08 - fy * sail_h, za + fu * yard_len)

    for i in range(nx):
        for j in range(ny):
            fu0, fu1, fy0, fy1 = i / nx, (i + 1) / nx, j / ny, (j + 1) / ny
            a0, a1, b0, b1 = cloth(fu0, fy1), cloth(fu0, fy0), cloth(fu1, fy1), cloth(fu1, fy0)
            c = (a0 + a1 + b0 + b1) / 4
            u = ((b0 + b1) - (a0 + a1)) / 2
            L = np.linalg.norm(u)
            u = u / L
            vp = ((a0 - a1) + (b0 - b1)) / 2
            H = np.linalg.norm(vp)
            v = norm(vp - np.dot(vp, u) * u)
            n = np.cross(u, v)
            if n[0] > 0:
                u, n = -u, -n
            cube = add_cube(sail, "sail_cloth_%d_%d" % (i, j), c, np.column_stack([u, v, n]), (L + 0.03, H + 0.03, 0.03),
                            {"all": None, "+3": "sail", "-3": "sail"}, world=False, stretch=True,
                            u_dir=v3(0, 0, 1), v_dir=v3(0, -1, 0))
            for f in ("north", "south"):
                cube.faces[f]["sub"] = (fu0, fy0, fu1, fy1)
    # triangle (u along the yard from its upper end, v downward) in [0,1] region coordinates
    sail_tri = [(0.3 / yard_len, 0.01), (16.4 / yard_len, 0.01), (7.9 / yard_len, 8.3 / sail_h)]

    # ---- oars: 8 per side, each its own bone pivoting at the oarlock
    oar_dir_down = math.radians(28)
    for side in (1, -1):
        sname = "l" if side > 0 else "r"   # l = port (gauche), r = starboard (droite)
        group = Bone("oars_" + ("left" if side > 0 else "right"), parent=root)
        for i, z in enumerate(OAR_Z):
            pivot = v3(side * (hp.half_width(z) + 0.04), hp.rail_y(z) - 0.32, z)
            ob = Bone("oar_%s%d" % (sname, i + 1), origin=pivot, parent=group)
            dvec = v3(side * math.cos(oar_dir_down), -math.sin(oar_dir_down), 0)
            beam(ob, "oar_shaft_%s%d" % (sname, i + 1), pivot - dvec * 1.3, pivot + dvec * 3.1, 0.16, "oar")
            beam(ob, "oar_blade_%s%d" % (sname, i + 1), pivot + dvec * 2.8, pivot + dvec * 4.15, 0.08, "oar",
                 width=0.5, up=v3(0, 0, 1))
            add_cube(ob, "oarlock_%s%d" % (sname, i + 1), pivot, np.eye(3), (0.2, 0.16, 0.2), "iron")

    # ---- stern streamer (long red pennant)
    s_root = stern_top + v3(0, 0.55, 0.1)
    parent = stern
    prev = s_root
    segs = []
    for j in range(3):
        b = Bone("streamer_%d" % (j + 1), origin=prev, parent=parent)
        seg_end = prev + v3(0, -0.12 - 0.08 * j, -0.75)
        h = 0.36 - 0.08 * j
        mid = (prev + seg_end) / 2
        u = norm(seg_end - prev)
        axes = np.column_stack([v3(1, 0, 0), np.cross(u, v3(1, 0, 0)), u])
        add_cube(b, "streamer_cloth_%d" % (j + 1), mid + v3(0, -h / 2, 0), axes,
                 (0.03, h, np.linalg.norm(seg_end - prev) + 0.04),
                 {"all": None, "+1": "flag", "-1": "flag"}, stretch=True)
        segs.append(b)
        parent, prev = b, seg_end

    # ---- lanterns (glow_* elements are rendered full bright)
    lantern_spots = [v3(1.05, 0, -9.15), v3(-1.05, 0, -9.15), v3(1.0, 0, 8.7), v3(-1.0, 0, 8.7)]
    for k, p in enumerate(lantern_spots):
        z = p[2]
        x = math.copysign(hp.half_width(z) + 0.18, p[0])
        base = v3(x, hp.rail_y(z) + 0.1, z)
        beam(lanterns, "lantern_pole_%d" % k, base + v3(0, -0.3, 0), base + v3(0, 0.75, 0), 0.08, "iron")
        add_cube(lanterns, "lantern_%d" % k, base + v3(0, 0.95, 0), np.eye(3), (0.42, 0.55, 0.42),
                 {"all": "lantern", "+2": "iron", "-2": "iron"}, stretch=True)
        add_cube(lanterns, "glow_lantern_%d" % k, base + v3(0, 0.95, 0), np.eye(3), (0.28, 0.4, 0.28), "glow",
                 stretch=True)

    # ---- rigging
    top = v3(0, MAST_TOP - 0.35, MAST_Z)
    rope_th = 0.06
    rigging = [
        ("shroud_p1", top, v3(hp.half_width(-1.0) + 0.02, hp.rail_y(-1.0), -1.0)),
        ("shroud_p2", top, v3(hp.half_width(-2.6) + 0.02, hp.rail_y(-2.6), -2.6)),
        ("shroud_s1", top, v3(-hp.half_width(-1.0) - 0.02, hp.rail_y(-1.0), -1.0)),
        ("shroud_s2", top, v3(-hp.half_width(-2.6) - 0.02, hp.rail_y(-2.6), -2.6)),
        ("forestay", top, stem_top + v3(0, 0.1, -0.1)),
        ("backstay", top, stern_top + v3(0, 0.1, 0.1)),
        ("halyard", v3(0.12, MAST_TOP - 0.2, MAST_Z), v3(0.2, yard_origin[1] + 0.1, MAST_Z)),
        ("tack", YARD_B + v3(0, -0.1, 0), v3(0.3, hp.rail_y(9.0), 9.0)),
        ("brace", YARD_A + v3(0, -0.1, 0), v3(hp.half_width(-8.0), hp.rail_y(-8.0), -8.0)),
        ("sheet", yard_origin + v3(0, -8.5, -0.6), v3(hp.half_width(-3.4), hp.rail_y(-3.4), -3.4)),
    ]
    for name, a, b in rigging:
        beam(ropes, "rope_" + name, a, b, rope_th, "rope")

    return root, sail_tri


# ---------------------------------------------------------------- animations
def kf(channel, t, xyz, interp="linear"):
    return {"channel": channel, "data_points": [{"x": str(round(xyz[0], 3)), "y": str(round(xyz[1], 3)),
                                                 "z": str(round(xyz[2], 3))}],
            "uuid": new_uuid(), "time": round(t, 4), "color": -1, "interpolation": interp}


def rot_kf(t, bb_euler_deg, interp="linear"):
    """Keyframe value producing the given additive bb Euler (a, b, c)."""
    return kf("rotation", t, bb_euler_deg, interp)


def animation(name, length, loop, tracks):
    animators = {}
    for bone, kfs in tracks:
        animators[bone.uuid] = {"name": bone.name, "type": "bone", "keyframes": kfs}
    return {"uuid": new_uuid(), "name": name, "loop": loop, "override": False, "length": length,
            "snapping": 20, "selected": False, "saved": True, "path": "", "anim_time_update": "",
            "blend_weight": "", "start_delay": "", "loop_delay": "", "animators": animators}


def find(root, name):
    if root.name == name:
        return root
    for c in root.children:
        r = find(c, name)
        if r:
            return r
    return None


def verify_oar_signs(root):
    """Check (numerically) that sweep>0 moves blades towards the bow and lift>0 raises them."""
    for name, side in (("oar_l1", 1), ("oar_r1", -1)):
        b = find(root, name)
        tip_local = v3(side * 3.5, -1.6, 0)  # relative to the pivot in ship space
        tip_bb = M @ tip_local
        for sweep, lift in ((20, 0), (0, 20)):
            be, ga = oar_euler(side, sweep, lift)
            R = euler_zyx_matrix((0, be, ga))
            moved = M @ (R @ tip_bb)
            if sweep:
                assert moved[2] > tip_local[2] + 0.5, (name, "sweep sign")
            if lift:
                assert moved[1] > tip_local[1] + 0.5, (name, "lift sign")


def oar_euler(side, sweep, lift):
    """bb Euler (beta, gamma) for an oar: sweep>0 = blade towards the bow, lift>0 = blade up."""
    if side > 0:   # port: blade at bb -x
        return -sweep, -lift
    return sweep, lift


def build_animations(root):
    anims = []
    # rowing cycle: catch -> drive -> release -> recovery
    cycle = [(0.0, 24, 0), (0.9, -24, 0), (1.1, -26, 13), (1.8, 22, 13), (2.0, 24, 0)]
    tracks = []
    for side, prefix in ((1, "oar_l"), (-1, "oar_r")):
        for i in range(8):
            b = find(root, "%s%d" % (prefix, i + 1))
            kfs = []
            for t, sweep, lift in cycle:
                be, ga = oar_euler(side, sweep, lift)
                kfs.append(rot_kf(t, (0, be, ga)))
            tracks.append((b, kfs))
    anims.append(animation("row", 2.0, "loop", tracks))

    sail = find(root, "sail")
    anims.append(animation("sail_wind", 3.0, "loop", [(sail, [
        rot_kf(0.0, (0, 0, 0), "catmullrom"), rot_kf(0.75, (0, 0, 3.0), "catmullrom"),
        rot_kf(1.5, (0, 0, 0.5), "catmullrom"), rot_kf(2.25, (0, 0, -1.5), "catmullrom"),
        rot_kf(3.0, (0, 0, 0), "catmullrom")])]))
    anims.append(animation("sail_furl", 1.0, "hold", [(sail, [
        kf("scale", 0.0, (1, 1, 1)), kf("scale", 1.0, (1, 0.06, 0.92))])]))

    # steer: t = 0 -> full port helm (turn left), 1 -> centre, 2 -> full starboard (turn right)
    tracks = []
    for n in ("rudder_p", "rudder_s"):
        b = find(root, n)
        tracks.append((b, [rot_kf(0.0, (0, -28, 0)), rot_kf(1.0, (0, 0, 0)), rot_kf(2.0, (0, 28, 0))]))
    anims.append(animation("steer", 2.0, "hold", tracks))

    f, ft = find(root, "flag"), find(root, "flag_tip")
    anims.append(animation("flag_wave", 1.2, "loop", [
        (f, [rot_kf(0, (0, 10, 0), "catmullrom"), rot_kf(0.6, (0, -10, 0), "catmullrom"),
             rot_kf(1.2, (0, 10, 0), "catmullrom")]),
        (ft, [rot_kf(0, (0, -18, 0), "catmullrom"), rot_kf(0.6, (0, 18, 0), "catmullrom"),
              rot_kf(1.2, (0, -18, 0), "catmullrom")])]))
    tracks = []
    for j in range(3):
        b = find(root, "streamer_%d" % (j + 1))
        amp = 9 + 6 * j
        sign = 1 if j % 2 == 0 else -1
        kfs = [rot_kf(k * 0.4, (amp * 0.12 * sign * (-1) ** k, amp * sign * (-1) ** k, 0), "catmullrom")
               for k in range(5)]
        tracks.append((b, kfs))
    anims.append(animation("streamer_wave", 1.6, "loop", tracks))
    return anims


# ---------------------------------------------------------------- export
def face_uv(cube, bbface, spec, rng_seed):
    rname = spec["region"]
    u0, v0, rw, rh = REGIONS[rname]
    normal, udir, vdir = FACE_AXES[bbface]
    # face dimensions (blocks) along its u / v axes, in cube space (bb axes, sizes are axis aligned)
    size_bb = cube.size  # bb x,y,z extents correspond to sizes 0,1,2
    du = abs(np.dot(udir, size_bb))
    dv = abs(np.dot(vdir, size_bb))
    if spec["stretch"]:
        su, sv = rw, rh
        ou, ov = 0, 0
    else:
        su = min(rw, max(1, round(du * 16 * spec["density"])))
        sv = min(rh, max(1, round(dv * 16 * spec["density"])))
        ou = (rng_seed * 7) % max(1, rw - su + 1)
        ov = ((rng_seed // 3) * 4) % max(1, rh - sv + 1)
        ov -= ov % 4
    uv = [u0 + ou, v0 + ov, u0 + ou + su, v0 + ov + sv]
    if spec.get("sub") is not None:
        s0 = spec["sub"]
        uv = [u0 + s0[0] * rw, v0 + s0[1] * rh, u0 + s0[2] * rw, v0 + s0[3] * rh]
    # orientation hints (given in bone-frame ship-local space): flip u / v if needed
    Rbb = to_bb_rot(cube.axes)
    for idx, hint, axis in ((0, spec["u_dir"], udir), (1, spec["v_dir"], vdir)):
        if hint is None:
            continue
        world_axis = M @ (Rbb @ axis)  # back to ship-local space
        if np.dot(world_axis, hint) < 0:
            uv[idx], uv[idx + 2] = uv[idx + 2], uv[idx]
    return uv


def export(root, anims, texture_png_bytes, out_paths):
    elements = []

    def group_json(b):
        children = []
        for c in b.cubes:
            Rbb = to_bb_rot(c.axes)
            euler = matrix_to_euler_zyx(Rbb)
            center = to_bb_point(c.center)
            half = c.size * 8.0
            frm = [round(center[k] - half[k], 4) for k in range(3)]
            to = [round(center[k] + half[k], 4) for k in range(3)]
            faces = {}
            for bbface, spec in c.faces.items():
                if spec is None:
                    faces[bbface] = {"uv": [0, 0, 0, 0], "texture": None}
                else:
                    seed = zlib.crc32((c.name + bbface).encode()) % 9973
                    faces[bbface] = {"uv": face_uv(c, bbface, spec, seed), "texture": 0}
            el = {"name": c.name, "box_uv": False, "rescale": False, "locked": False,
                  "render_order": "default", "allow_mirror_modeling": True,
                  "from": frm, "to": to, "autouv": 0, "color": 0, "origin": center,
                  "faces": faces, "type": "cube", "uuid": c.uuid}
            if any(abs(x) > 1e-4 for x in euler):
                el["rotation"] = euler
            elements.append(el)
            children.append(c.uuid)
        for ch in b.children:
            children.append(group_json(ch))
        g = {"name": b.name, "origin": to_bb_point(b.origin), "color": 0, "uuid": b.uuid, "export": True,
             "mirror_uv": False, "isOpen": False, "locked": False, "visibility": True, "autouv": 0,
             "children": children}
        e = matrix_to_euler_zyx(to_bb_rot(b.rot))
        if any(abs(x) > 1e-4 for x in e):
            g["rotation"] = e
        return g

    outliner = [group_json(root)]
    tex_b64 = base64.b64encode(texture_png_bytes).decode()
    model = {
        "meta": {"format_version": "4.10", "model_format": "free", "box_uv": False},
        "name": "galley",
        "model_identifier": "galley",
        "visible_box": [24, 16, 0],
        "variable_placeholders": "",
        "variable_placeholder_buttons": [],
        "timeline_setups": [],
        "unhandled_root_fields": {},
        "resolution": {"width": SIZE, "height": SIZE},
        "elements": elements,
        "outliner": outliner,
        "textures": [{
            "path": "", "name": "galley.png", "folder": "entity", "namespace": "medievalships", "id": "0",
            "group": "", "width": SIZE, "height": SIZE, "uv_width": SIZE, "uv_height": SIZE,
            "particle": False, "use_as_default": True, "layers_enabled": False, "sync_to_project": "",
            "render_mode": "default", "render_sides": "auto", "frame_time": 1, "frame_order_type": "loop",
            "frame_order": "", "frame_interpolate": False, "visible": True, "internal": True, "saved": True,
            "uuid": new_uuid(), "relative_path": "../src/main/resources/assets/medievalships/textures/entity/galley.png",
            "source": "data:image/png;base64," + tex_b64}],
        "animations": anims,
    }
    for p in out_paths:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w") as f:
            json.dump(model, f, separators=(",", ":") if "resources" in p else (", ", ": "),
                      indent=None if "resources" in p else 1)
    return model


def main():
    root, sail_tri = build()
    verify_oar_signs(root)
    anims = build_animations(root)
    tex_path = os.path.join(ROOT, "src/main/resources/assets/medievalships/textures/entity/galley.png")
    make_texture(tex_path, sail_tri)
    with open(tex_path, "rb") as f:
        png = f.read()
    model = export(root, anims, png, [
        os.path.join(ROOT, "blockbench/galley.bbmodel"),
        os.path.join(ROOT, "src/main/resources/assets/medievalships/models/entity/galley.bbmodel"),
    ])
    n_groups = [0]

    def count(g):
        n_groups[0] += 1
        for c in g["children"]:
            if isinstance(c, dict):
                count(c)
    count(model["outliner"][0])
    print("cubes:", len(model["elements"]), "bones:", n_groups[0], "animations:",
          [a["name"] for a in model["animations"]])


if __name__ == "__main__":
    main()
