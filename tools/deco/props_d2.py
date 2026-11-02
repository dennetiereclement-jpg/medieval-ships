"""D2's four street decorations (1.20.0) on decolib: the herb drying rack (deco_sechoir), the hanging lantern
(deco_lanterne), the crown banner (deco_banniere) and the shade sails (deco_ombrage).

Each build_<id>(root, det) draws one decoration (prop-local blocks, y up, +z = the front, towards the player who
placed it, the anchor block's centre at (0, 0, 0)); tools/deco/generate_<id>.py calls it and exports. The helpers
here complete decolib's (never edited): squared beams and collars, bolts, a herb bundle looped over a beam, the big
wooden-framed lantern, a shade sail whose edges sag between the corners, the gold fittings of the banner arm. The
extra atlas regions they use (denser herb bundles, the crown banner with a bold lion) come from atlas_d2.py.
"""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import decolib as dl  # noqa: E402

gg = dl.gg
v3, norm, Bone, add_cube, beam, loft = dl.v3, dl.norm, dl.Bone, dl.add_cube, dl.beam, dl.loft
EYE, UP, X, Z = dl.EYE, dl.UP, dl.X, dl.Z
collide = dl.collide


# ---------------------------------------------------------------- small helpers
def box(bone, name, lo, hi, region, **kw):
    lo, hi = v3(*lo), v3(*hi)
    return add_cube(bone, name, (lo + hi) / 2, EYE, hi - lo, region, **kw)


def cbox(bone, name, c, size, region, **kw):
    """A box centred on c."""
    c, s = v3(*c), v3(*size)
    return add_cube(bone, name, c, EYE, s, region, **kw)


def hbeam(bone, name, x0, x1, y0, y1, z, depth, region="plank", ends="end_grain"):
    """A horizontal squared beam along x (grain along x), from x0 to x1, y0 to y1, centred on z."""
    return add_cube(bone, name, ((x0 + x1) / 2, (y0 + y1) / 2, z), EYE, (x1 - x0, y1 - y0, depth),
                    {"all": region, "+1": ends, "-1": ends}, u_dir=X)


def bolt(bone, name, p, normal=(0, 0, 1), s=0.065):
    """An iron bolt head on a face (p on the face, normal outwards)."""
    p, n = v3(*p), v3(*normal)
    size = [s, s, s]
    size[int(np.argmax(np.abs(n)))] = 0.03
    return cbox(bone, name, p + n * 0.012, size, "iron_dark")


def collar(bone, name, c, d, h, region="iron_band", top="iron"):
    """A band / sleeve round a squared post (section d, centred on c, h high)."""
    return cbox(bone, name, c, (d, h, d), {"all": region, "+2": top, "-2": top}, u_dir=X)


# ---------------------------------------------------------------- herb bundle
def herb_bundle(bone, det, name, under, region, length, width, rope_len, beam_d=0.36, planes=3, phase=0.0):
    """A bundle of herbs hanging under a beam (under = the point under the beam's lower face): the rope looped over
    the beam (a band round it, two strands down), the tie wrap, the cut stems sticking up, the bunch as `planes`
    crossed cut-out planes (the region's tie at the top). Returns the bundle's bottom point."""
    top = v3(*under)
    tie = top - UP * rope_len
    for k, dz in enumerate((-0.04, 0.04)):
        beam(det, "%s_rope_%d" % (name, k), top + v3(0, 0.02, dz * 2.5), tie + v3(0, 0.03, dz * 0.4), 0.035, "rope", extend=0.015)
    cbox(det, name + "_loop", top + UP * 0.19, (0.07, 0.4, beam_d + 0.035), {"all": "rope", "+2": "rope_coil"})
    add_cube(bone, name + "_tie", tie, gg.ry(0.3 + phase), (0.12, 0.12, 0.12), {"all": "rope_coil", "+2": "rope", "-2": "rope"},
             u_dir=X)
    add_cube(det, name + "_stems", tie + UP * 0.1, gg.ry(0.3 + phase), (0.085, 0.1, 0.085), {"all": "herb_stems", "+2": "end_grain"})
    c = tie - UP * (length / 2 - 0.02)
    for k in range(planes):
        a = phase + math.pi * k / planes
        R = gg.ry(a)
        add_cube(bone, "%s_bunch_%d" % (name, k), c, R, (width, length, 0.004), {"all": None, "+3": region, "-3": region},
                 stretch=True, u_dir=R[:, 0], v_dir=-UP)
    return tie - UP * length


# ---------------------------------------------------------------- the big lantern
def big_lantern(bone, det, name, top, w=0.84, h=0.74):
    """The big wooden-framed street lantern: top = the end of its chain. A ring and a small roof, a wide cap with iron
    corners, the lit glass (2 x 2 panes a side, drawn full bright) between four corner posts with a middle rail and
    mullions, a wide base with iron corners, a pendant and a short drop with a hook under it. Returns its bottom."""
    top = v3(*top)
    cx, cz = top[0], top[2]
    yr = top[1]
    cbox(det, name + "_ring", (cx, yr - 0.05, cz), (0.035, 0.1, 0.1), "iron_dark")
    cbox(bone, name + "_roof", (cx, yr - 0.15, cz), (0.36, 0.1, 0.36), {"all": "wood_dark", "+2": "iron"})
    cbox(bone, name + "_roof_plate", (cx, yr - 0.235, cz), (w * 0.86, 0.07, w * 0.86), {"all": "wood_dark", "+2": "plank"})
    y_cap = yr - 0.27
    cbox(bone, name + "_cap", (cx, y_cap - 0.075, cz), (w + 0.2, 0.15, w + 0.2), {"all": "wood_dark", "+2": "plank", "-2": "plank"})
    y1 = y_cap - 0.15
    y0 = y1 - h
    ym = (y0 + y1) / 2
    cbox(bone, "glow_" + name + "_glass", (cx, ym, cz), (w - 0.08, h, w - 0.08), {"all": "lantern_grid", "+2": "glow", "-2": "glow"})
    for k, (sx, sz) in enumerate(((1, 1), (1, -1), (-1, 1), (-1, -1))):
        cbox(bone, "%s_post_%d" % (name, k), (cx + sx * (w / 2 - 0.05), ym, cz + sz * (w / 2 - 0.05)), (0.1, h, 0.1), "wood", u_dir=UP)
    cbox(det, name + "_rail", (cx, ym, cz), (w - 0.04, 0.06, w - 0.04), "wood", u_dir=X)
    cbox(det, name + "_mull_x", (cx, ym, cz), (w - 0.04, h, 0.05), "wood", u_dir=UP)
    cbox(det, name + "_mull_z", (cx, ym, cz), (0.05, h, w - 0.04), "wood", u_dir=UP)
    cbox(bone, name + "_base", (cx, y0 - 0.07, cz), (w + 0.12, 0.14, w + 0.12), {"all": "wood_dark", "+2": "plank", "-2": "plank"})
    for k, (sx, sz) in enumerate(((1, 1), (1, -1), (-1, 1), (-1, -1))):
        cbox(det, "%s_iron_top_%d" % (name, k), (cx + sx * (w / 2 + 0.065), y_cap - 0.075, cz + sz * (w / 2 + 0.065)), (0.11, 0.17, 0.11), "iron")
        cbox(det, "%s_iron_bot_%d" % (name, k), (cx + sx * (w / 2 + 0.025), y0 - 0.07, cz + sz * (w / 2 + 0.025)), (0.1, 0.16, 0.1), "iron")
    cbox(bone, name + "_pendant", (cx, y0 - 0.2, cz), (0.3, 0.12, 0.3), {"all": "wood_dark", "+2": "plank", "-2": "iron"})
    cbox(det, name + "_pendant_tip", (cx, y0 - 0.3, cz), (0.14, 0.08, 0.14), "iron_dark")
    end = dl.chain(det, name + "_drop", (cx, y0 - 0.34, cz), 0.2, link=0.1, w=0.07)
    cbox(det, name + "_hook", end, (0.1, 0.04, 0.04), "iron_dark")
    return end


# ---------------------------------------------------------------- cloth
def shade_sail(bone, name, c00, c10, c01, c11, sag=0.3, edge_sag=0.1, nx=6, ny=5, region="sail", ripple=0.025, th=0.03):
    """A shade sail tied at four corners (c00 = (s0, t0), c10 = (s1, t0), c01 = (s0, t1), c11 = (s1, t1)): the cloth
    bellies down in the middle and its edges droop between the corners (catenary-like), with a soft ripple. No
    collision. Returns P(s, t)."""
    c00, c10, c01, c11 = (v3(*p) for p in (c00, c10, c01, c11))

    def P(s, t):
        p = (c00 * (1 - s) + c10 * s) * (1 - t) + (c01 * (1 - s) + c11 * s) * t
        ss, st = math.sin(math.pi * s), math.sin(math.pi * t)
        drop = sag * ss * st + edge_sag * (ss + st - 2 * ss * st)
        return p - UP * drop + UP * (ripple * ss * st * math.sin(s * 8.0 + t * 5.0 + 0.6))
    loft(bone, name, P, nx, ny, region, th=th)
    return P


def tie_rope(bone, name, a, b, d=0.045, sag=0.03, segs=2, knot=True, detail=None):
    """A short rope from a post binding (a) to a sail corner (b), sagging a little, a knot at the corner."""
    line = dl.sag_rope(bone, name, a, b, sag=sag, segs=segs, d=d)
    if knot:
        dl.knot(detail if detail is not None else bone, name + "_knot", b, s=0.1)
    return line
