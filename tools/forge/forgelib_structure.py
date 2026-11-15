"""Library of the divine forge STRUCTURE (1.34.0): tools/forge/generate_forge_divine.py builds the model with it.

    import forgelib_structure as fl
    f = fl.Forge("forge_divine", size=512)          # own atlas, root bone, materials painted on creation
    b = f.bone("body")                              # a static sub-bone (cooked into the static mesh)
    f.box(b, "wall", (x0, y0, z0), (x1, y1, z1), "stone", faces={"+z": "stone_dark", "-y": None})
    f.rbox(b, "arch", centre, angle_deg, (sx, sy, sz), "stone")       # a box turned about z (arches, gear parts)
    f.pipe(b, "pipe_l", [p0, p1, p2], s=0.28)       # axis-aligned copper run: elbows, flanges, end caps
    f.gear(f.bone("gear_a_0", origin=c), c, ...)    # opaque gear, pivot = centre
    f.export(icon=fn)                               # cull + resolve, .bbmodel (assets + blockbench), texture

COORDINATES: blocks, origin = centre of the anchor block, y = 0 on the ground, +z = the FRONT, +x = right seen from
the front (the contract of tools/forge/CALAGE.md and of the workshops). Texture density 16 px per block, every
material face anchored on world coordinates (bricks continue from one cube to the next).

RULES (checked by tools/forge/forge_audit.py on export, must print DEFECTS = 0):
- no two parallel overlapping faces closer than 1/64 block, in any visibility configuration (static + craft_* +
  frame k of every flipbook, gears at 0 and 45 degrees); faces hidden inside the same rigid set are removed
  (cull) and the remaining conflicts are separated by growing / shrinking one cube by 1/32 (resolve);
- no cube thinner than 1/64; every texel of the atlas is opaque (no cut-out in the structure);
- glow cubes (full bright) are named glow*.
"""
import copy
import json
import math
import os
import random
import re
import sys
import zlib

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(TOOLS, "tents"))
sys.path.insert(0, os.path.join(TOOLS, "doors"))
sys.path.insert(0, TOOLS)
sys.path.insert(0, HERE)
import tentlib as tl  # noqa: E402
import doorlib_large as dl  # noqa: E402
import door_audit_large as DA  # noqa: E402

gg, gn = tl.gg, tl.gn
Bone, EYE, v3 = tl.Bone, tl.EYE, tl.v3
ASSETS, ROOT = tl.ASSETS, tl.ROOT
SCRATCH = "/tmp/claude-0/-home-user-medieval-ships/2a9b6be4-7c0a-5b40-ad8d-40cfe82b9e67/scratchpad"
OUT = os.path.join(SCRATCH, "forge_out")
REF = os.path.join(SCRATCH, "forge_ref/forge.png")
MIN_GAP = 1.0 / 64
STEP = 1.0 / 32
FRAME_RE = re.compile(r"^(.*)_f(\d+)$")
SEM = {"+x": "west", "-x": "east", "+y": "up", "-y": "down", "+z": "north", "-z": "south"}
AXES6 = {"+x": (0, 1), "-x": (0, -1), "+y": (1, 1), "-y": (1, -1), "+z": (2, 1), "-z": (2, -1)}
BB2SEM = {v: k for k, v in SEM.items()}
rgb, mix, shade = dl.rgb, dl.mix, dl.shade

# ---------------------------------------------------------------- palette (sampled on the reference picture)
STONE, STONE_L, STONE_D, MORTAR = rgb("6f6765"), rgb("968c88"), rgb("4c4543"), rgb("2e2928")
DSTONE, DSTONE_L, DMORTAR = rgb("4b3a34"), rgb("675048"), rgb("221917")
CARVED, CARVED_L, CARVED_D = rgb("85797a"), rgb("aca09c"), rgb("4a4242")
GOLD, GOLD_L, GOLD_D = rgb("cf9636"), rgb("f6d06c"), rgb("7a5016")
BRONZE, BRONZE_L, BRONZE_D = rgb("9c6a2a"), rgb("c99446"), rgb("4e3010")
COPPER, COPPER_L, COPPER_D = rgb("ae5f38"), rgb("e99a62"), rgb("5c2a16")
IRON, IRON_L, IRON_D = rgb("2d2829"), rgb("4c4546"), rgb("151213")
WOOD, WOOD_L, WOOD_D = rgb("94592a"), rgb("bb7a3c"), rgb("4a2a12")
WOODG, WOODG_L, WOODG_D = rgb("c38c3a"), rgb("e9b660"), rgb("7a521e")
BLACK, BLACK_L, BLACK_D = rgb("252123"), rgb("3c3638"), rgb("0f0d0e")
FIRE_W, FIRE_Y, FIRE_O, FIRE_R = rgb("fff3c4"), rgb("ffd04a"), rgb("ff9a24"), rgb("e65e12")


# ---------------------------------------------------------------- painters (dl.Px over a tile)
def p_bricks(base, light, mortar, bw=8, bh=4, noise=5, seed_shift=3):
    def paint(px):
        rows = (px.h + bh - 1) // bh
        for r in range(rows):
            off = (r % 2) * (bw // 2)
            i = -off
            while i < px.w:
                w = bw + px.rng.choice((-1, 0, 0, 1)) if bw > 6 else bw
                tone = px.jit(base, 7)
                for jj in range(bh):
                    j = r * bh + jj
                    if j >= px.h:
                        break
                    for ii in range(w):
                        x = i + ii
                        if x < 0 or x >= px.w:
                            continue
                        if jj == bh - 1 or ii == w - 1:
                            c = mortar
                        elif jj == 0 or ii == 0:
                            c = mix(tone, light, 0.45)
                        elif jj == bh - 2:
                            c = shade(tone, 0.88)
                        else:
                            c = tone
                            if px.rng.random() < 0.06:
                                c = shade(tone, 0.82)
                        px.put(x, j, px.jit(c, noise))
                i += w
    return paint


def p_carved(base, light, dark, cell=16):
    """Chiselled stone blocks: bevel light top-left, dark bottom-right, inner panel."""
    def paint(px):
        for j in range(px.h):
            for i in range(px.w):
                a, b = i % cell, j % cell
                c = base
                if a == 0 or b == 0:
                    c = light
                elif a == cell - 1 or b == cell - 1:
                    c = dark
                elif a == 1 or b == 1:
                    c = mix(base, light, 0.4)
                elif a == cell - 2 or b == cell - 2:
                    c = mix(base, dark, 0.4)
                elif (a in (3, cell - 4) and 3 <= b <= cell - 4) or (b in (3, cell - 4) and 3 <= a <= cell - 4):
                    c = shade(base, 0.86)
                px.put(i, j, px.jit(c, 5))
    return paint


def p_floor(base, light, dark, cell=16):
    def paint(px):
        for j in range(px.h):
            for i in range(px.w):
                a, b = i % cell, j % cell
                ti, tj = i // cell, j // cell
                tone = shade(base, 0.92 + 0.12 * ((ti * 7 + tj * 3) % 5) / 4)
                c = tone
                if a == cell - 1 or b == cell - 1:
                    c = dark
                elif a == 0 or b == 0:
                    c = mix(tone, light, 0.5)
                elif (a + 2 * b + ti * 5) % 23 == 0:
                    c = shade(tone, 0.8)
                px.put(i, j, px.jit(c, 5))
    return paint


def p_metal(base, light, dark, rivet=8, plate=16):
    def paint(px):
        for j in range(px.h):
            for i in range(px.w):
                a, b = i % plate, j % plate
                c = base
                if b == 0:
                    c = light
                elif b == plate - 1:
                    c = dark
                if rivet and a % rivet == rivet // 2 and b % rivet == rivet // 2:
                    c = mix(light, (230, 220, 210), 0.3)
                elif rivet and a % rivet == rivet // 2 + 1 and b % rivet == rivet // 2 + 1:
                    c = dark
                px.put(i, j, px.jit(c, 4))
    return paint


def p_gold(base, light, dark, cell=16):
    def paint(px):
        for j in range(px.h):
            for i in range(px.w):
                a, b = i % cell, j % cell
                c = base
                if a == 0 or b == 0:
                    c = light
                elif a == cell - 1 or b == cell - 1:
                    c = dark
                elif (a + b) % 9 == 0:
                    c = mix(base, light, 0.5)
                elif (a * 3 + b * 5) % 17 == 0:
                    c = shade(base, 0.85)
                px.put(i, j, px.jit(c, 5))
    return paint


def p_band(base, light, dark, along_u=True, seam=16):
    """Pipe shading: the band runs along u (or v); across it: light streak near the top, dark at the bottom."""
    def paint(px):
        n = px.h if along_u else px.w
        L = px.w if along_u else px.h
        for a in range(n):
            t = a / max(1, n - 1)
            if t < 0.15:
                c = mix(base, dark, 0.3)
            elif t < 0.4:
                c = mix(base, light, 0.8 - abs(t - 0.27) * 3)
            elif t < 0.8:
                c = base
            else:
                c = mix(base, dark, (t - 0.8) * 4)
            for b in range(L):
                cc = c
                if b % seam == seam - 1:
                    cc = shade(c, 0.78)
                elif b % seam == 0:
                    cc = mix(c, light, 0.25)
                i, j = (b, a) if along_u else (a, b)
                px.put(i, j, px.jit(cc, 4))
    return paint


def p_ring(base, light, dark):
    def paint(px):
        cx, cy = px.w / 2, px.h / 2
        for j in range(px.h):
            for i in range(px.w):
                d = max(abs(i + 0.5 - cx), abs(j + 0.5 - cy)) / (px.w / 2)
                if d > 0.82:
                    c = mix(base, dark, 0.3)
                elif d > 0.62:
                    c = light if (i + j) % 5 else base
                elif d > 0.4:
                    c = base
                else:
                    c = mix(dark, (20, 12, 8), 0.5)
                px.put(i, j, px.jit(c, 4))
    return paint


def p_planks(base, light, dark, horizontal=True, size=4):
    def paint(px):
        n = px.h if horizontal else px.w
        L = px.w if horizontal else px.h
        for a in range(n):
            row = a // size
            tone = shade(base, 0.92 + 0.1 * ((row * 5) % 3) / 2)
            joint = (row * 11) % L
            for b in range(L):
                k = a % size
                c = tone
                if k == size - 1:
                    c = dark
                elif k == 0:
                    c = mix(tone, light, 0.4)
                elif (b + row * 3) % 7 == 0:
                    c = shade(tone, 0.9)
                if b == joint or b == (joint + L // 2) % L:
                    c = dark
                i, j = (b, a) if horizontal else (a, b)
                px.put(i, j, px.jit(c, 4))
    return paint


def p_drawers(n=2, wood=WOOD, light=WOOD_L, dark=WOOD_D, handle=IRON_L, cols=True):
    """n drawers side by side (cols) or stacked, each with a frame and a handle."""
    def paint(px):
        px.rect(0, px.w, 0, px.h, dark)
        for k in range(n):
            if cols:
                i0, i1, j0, j1 = int(k * px.w / n) + 1, int((k + 1) * px.w / n) - 1, 1, px.h - 1
            else:
                i0, i1, j0, j1 = 1, px.w - 1, int(k * px.h / n) + 1, int((k + 1) * px.h / n) - 1
            px.rect(i0, i1, j0, j1, wood, 5)
            px.rect(i0, i1, j0, j0 + 1, light, 3)
            px.rect(i0, i0 + 1, j0, j1, mix(wood, light, 0.5))
            px.rect(i0, i1, j1 - 1, j1, shade(wood, 0.75))
            ci, cj = (i0 + i1) // 2, (j0 + j1) // 2
            px.rect(ci - 2, ci + 2, cj, cj + 1, handle)
            px.put(ci - 2, cj - 1, mix(handle, (255, 255, 255), 0.3))
    return paint


def p_flat(c, noise=4):
    def paint(px):
        px.rect(0, px.w, 0, px.h, c, noise)
    return paint


def p_glow_bricks(base=rgb("ff8a1c"), light=rgb("ffd25a"), mortar=rgb("b8420c"), bw=8, bh=4):
    return p_bricks(base, light, mortar, bw, bh, noise=8)


def p_coal():
    def paint(px):
        for j in range(px.h):
            for i in range(px.w):
                r = px.rng.random()
                if r < 0.18:
                    c = FIRE_Y
                elif r < 0.45:
                    c = FIRE_O
                elif r < 0.75:
                    c = FIRE_R
                else:
                    c = rgb("8a2a0a")
                if j < 2:
                    c = mix(c, FIRE_W, 0.35)
                px.put(i, j, c)
    return paint


def p_fire(c1, c2):
    def paint(px):
        for j in range(px.h):
            for i in range(px.w):
                t = j / max(1, px.h - 1)
                c = mix(c1, c2, t)
                if px.rng.random() < 0.2:
                    c = mix(c, c1, 0.5)
                px.put(i, j, px.jit(c, 6))
    return paint


def p_glass(core=FIRE_W, mid=FIRE_Y, edge=FIRE_O):
    """Glowing glass of the heat columns (vertical streaks, bright core)."""
    def paint(px):
        for j in range(px.h):
            for i in range(px.w):
                x = abs(i + 0.5 - px.w / 2) / (px.w / 2)
                c = mix(mid, core, max(0, 0.5 - x) * 1.6) if x < 0.5 else mix(mid, edge, (x - 0.5) * 2)
                if (j + (i % 3) * 5) % 13 == 0:
                    c = mix(c, core, 0.5)
                if i == 0 or i == px.w - 1:
                    c = mix(edge, rgb("a0400c"), 0.4)
                px.put(i, j, px.jit(c, 5))
    return paint


def p_lava(cell=4):
    def paint(px):
        for j in range(px.h):
            for i in range(px.w):
                a, b = i % cell, j % cell
                if a == cell - 1 or b == cell - 1:
                    c = rgb("3a1a10")
                else:
                    t = px.rng.random()
                    c = FIRE_W if t < 0.12 else FIRE_Y if t < 0.55 else FIRE_O
                    if a == 0 and b == 0:
                        c = FIRE_W
                px.put(i, j, c)
    return paint


def p_gem():
    def paint(px):
        cx, cy = px.w / 2, px.h / 2
        for j in range(px.h):
            for i in range(px.w):
                d = max(abs(i + 0.5 - cx), abs(j + 0.5 - cy)) / (px.w / 2)
                c = FIRE_W if d < 0.35 else FIRE_Y if d < 0.7 else FIRE_O
                px.put(i, j, c)
    return paint


# ---------------------------------------------------------------- the builder
class Forge:
    def __init__(self, name, size=512):
        self.name, self.size = name, size
        tl.setup(name)
        self.atlas = dl.Atlas(size)
        self.regions = {}
        self.root = Bone(name)
        self.bones = {}
        self.counts = {}
        self.colliders = []

    # ------------------------------------------------ atlas
    def material(self, name, painter, w=64, h=64):
        r = self.atlas.alloc(name, w, h)
        painter(dl.Px(self.atlas.arr, r[0], r[1], w, h, zlib.crc32(name.encode())))
        self.regions[name] = r
        return name

    def bone(self, name, origin=(0, 0, 0), parent=None):
        b = Bone(name, origin=origin, parent=parent or self.root)
        self.bones[name] = b
        return b

    def _unique(self, nm):
        k = self.counts.get(nm, 0)
        self.counts[nm] = k + 1
        return nm if k == 0 else "%s_%d" % (nm, k)

    # ------------------------------------------------ cubes
    def box(self, bone, name, lo, hi, mat, faces=None, glow=False):
        lo, hi = np.minimum(lo, hi).astype(float), np.maximum(lo, hi).astype(float)
        size = np.maximum(hi - lo, MIN_GAP * 2)
        nm = self._unique(("glow_" if glow and not name.startswith("glow") else "") + name)
        specs = {}
        for sem in SEM:
            sp = mat
            if faces and sem in faces:
                sp = faces[sem]
            specs[SEM[sem]] = sp
        c = gg.Cube(bone, nm, (lo + hi) / 2, EYE.copy(), size, specs)
        c.orig = dict(specs)
        return c

    def rbox(self, bone, name, centre, angle, size, mat, faces=None, glow=False):
        """A box turned by `angle` degrees about z (local x = cos/sin direction)."""
        a = math.radians(angle)
        R = np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1.0]])
        nm = self._unique(("glow_" if glow and not name.startswith("glow") else "") + name)
        specs = {}
        for sem in SEM:
            sp = mat
            if faces and sem in faces:
                sp = faces[sem]
            specs[SEM[sem]] = sp
        c = gg.Cube(bone, nm, np.array(centre, float), R, np.maximum(np.array(size, float), MIN_GAP * 2), specs)
        c.orig = dict(specs)
        return c

    def collide(self, lo, hi):
        lo, hi = np.minimum(lo, hi), np.maximum(lo, hi)
        self.colliders.append([round(float(v), 3) for v in list(lo) + list(hi)])

    def pipe(self, bone, name, pts, s=0.28, flange=0.08, every=None, cap_start=True, cap_end=True, mat="copper",
             joint="copper_joint", ring="bronze"):
        """Axis-aligned copper run through the points: segments, elbow blocks at the corners (s + 2 flange), end
        caps, flanges every `every` blocks. Returns the end points' outer positions."""
        pts = [np.array(p, float) for p in pts]
        e = s + 2 * flange
        for i in range(len(pts) - 1):
            a, b = pts[i].copy(), pts[i + 1].copy()
            d = b - a
            k = int(np.argmax(np.abs(d)))
            sg = 1.0 if d[k] > 0 else -1.0
            if i > 0:
                a[k] += sg * (e / 2 - STEP)
            if i < len(pts) - 2:
                b[k] -= sg * (e / 2 - STEP)
            lo, hi = np.minimum(a, b), np.maximum(a, b)
            for j in range(3):
                if j != k:
                    lo[j], hi[j] = a[j] - s / 2, a[j] + s / 2
            faces = self._pipe_faces(k, mat)
            self.box(bone, "%s_%d" % (name, i), lo, hi, mat, faces=faces)
            if every:
                L = hi[k] - lo[k]
                n = int(L / every)
                for m in range(1, n + 1):
                    t = lo[k] + L * m / (n + 1)
                    flo, fhi = lo.copy(), hi.copy()
                    flo[k], fhi[k] = t - 0.045, t + 0.045
                    for j in range(3):
                        if j != k:
                            flo[j], fhi[j] = a[j] - e / 2 + 0.01, a[j] + e / 2 - 0.01
                    self.box(bone, "%s_ring_%d_%d" % (name, i, m), flo, fhi, ring)
        for i in range(1, len(pts) - 1):
            p = pts[i]
            self.box(bone, "%s_elbow_%d" % (name, i), p - e / 2, p + e / 2, joint)
        for idx, cap in ((0, cap_start), (len(pts) - 1, cap_end)):
            if not cap:
                continue
            p = pts[idx]
            q = pts[1] if idx == 0 else pts[-2]
            d = p - q
            k = int(np.argmax(np.abs(d)))
            sg = 1.0 if d[k] > 0 else -1.0
            lo, hi = p - e / 2 + 0.01, p + e / 2 - 0.01
            lo[k], hi[k] = sorted((p[k] - sg * 0.1, p[k] + sg * 0.03))
            self.box(bone, "%s_cap_%d" % (name, idx), lo, hi, ring, faces={("+" if sg > 0 else "-") + "xyz"[k]: "copper_end"})

    @staticmethod
    def _pipe_faces(k, mat):
        """Band orientation per face: the pipe axis k (0 x, 1 y, 2 z)."""
        axis_u = {"north": 0, "south": 0, "west": 2, "east": 2, "up": 0, "down": 0}
        out = {}
        for sem, bb in SEM.items():
            if AXES6[sem][0] == k:
                out[sem] = "copper_end"
            else:
                out[sem] = ("band", mat + ("_u" if axis_u[bb] == k else "_v"))
        return out

    def gear(self, bone, c, r_out=0.5, r_in=0.36, teeth=10, tooth_len=0.13, tooth_w=0.16, phase=18.0,
             depth=9.0 / 64, mat="gold", dark="gold_dark", gem="gem", spokes=4):
        """Opaque gear in the xy plane centred on c (its bone pivots there): octagonal ring (8 turned segments,
        alternate depths so their overlaps never share a plane), teeth, spokes, hub, glowing gem."""
        c = np.array(c, float)
        zc = c[2]
        r_mid, t = (r_out + r_in) / 2, r_out - r_in
        L = 2 * r_out * math.tan(math.radians(22.5)) + 0.02
        for k in range(8):
            a = k * 45.0
            d = depth - (0 if k % 2 == 0 else 2.0 / 64) - 2.0 / 64
            ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
            self.rbox(bone, "ring_%d" % k, c + np.array([ca * r_mid, sa * r_mid, 0]), a, (t, L, 2 * d),
                      mat if k % 2 == 0 else mat)
        for k in range(teeth):
            a = phase + k * 360.0 / teeth
            ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
            r0, r1 = r_out - 0.07, r_out + tooth_len
            self.rbox(bone, "tooth_%d" % k, c + np.array([ca * (r0 + r1) / 2, sa * (r0 + r1) / 2, 0]), a,
                      (r1 - r0, tooth_w, 2 * depth), mat)
        hub = 0.15
        for k in range(spokes):
            a = k * 360.0 / spokes
            ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
            r0, r1 = hub - 0.04, r_in + 0.05
            self.rbox(bone, "spoke_%d" % k, c + np.array([ca * (r0 + r1) / 2, sa * (r0 + r1) / 2, 0]), a,
                      (r1 - r0, 0.11, 2 * (depth - 5.0 / 64)), dark)
        self.box(bone, "hub", c + np.array([-hub, -hub, -depth - 2.0 / 64]), c + np.array([hub, hub, depth + 2.0 / 64]), mat)
        g = 0.065
        self.box(bone, "glow_gem", c + np.array([-g, -g, depth]), c + np.array([g, g, depth + 4.0 / 64]), gem)

    # ------------------------------------------------ groups (visibility / rigid sets)
    @staticmethod
    def group_of(bone):
        b = bone
        while b is not None:
            m = FRAME_RE.match(b.name)
            if m:
                return ("frame", m.group(1), int(m.group(2)))
            if b.name.startswith("craft_"):
                return ("craft", b.name)
            if b.name.startswith("gear_"):
                return ("gear", b.name)
            b = b.parent
        return ("static",)

    @staticmethod
    def compatible(g1, g2):
        if g1[0] == "frame" and g2[0] == "frame" and g1[1] == g2[1] and g1[2] != g2[2]:
            return False
        return True

    @staticmethod
    def coverer_ok(face_group, cov_group):
        if face_group[0] == "gear":
            return cov_group == face_group
        if cov_group[0] == "static":
            return True
        return cov_group == face_group

    def cubes(self):
        return list(tl._all_cubes(self.root))

    # ------------------------------------------------ faces in a pose
    def _pose_RC(self, c, ang, center=None):
        R = np.asarray(c.axes, float)
        C = np.asarray(c.center if center is None else center, float)
        if ang and c.group[0] == "gear":
            a = math.radians(ang)
            Rz = np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1.0]])
            piv = np.asarray(c.gbone.origin, float)
            C = Rz @ (C - piv) + piv
            R = Rz @ R
        return R, C

    def _faces(self, c, ang, center=None, size=None):
        R, C = self._pose_RC(c, ang, center)
        h = np.asarray(c.size if size is None else size, float) / 2
        out = []
        for sem, (k, s) in AXES6.items():
            bb = SEM[sem]
            if c.faces.get(bb) is None:
                continue
            o = [j for j in range(3) if j != k]
            n = R[:, k] * s
            p = C + n * h[k]
            e1, e2 = R[:, o[0]] * h[o[0]], R[:, o[1]] * h[o[1]]
            sg = 1
            for x in n:
                if abs(x) > 1e-3:
                    sg = 1 if x > 0 else -1
                    break
            cn = n * sg
            out.append(dict(cube=c, sem=sem, bb=bb, k=k, s=s, n=n, centre=p, area=4 * h[o[0]] * h[o[1]],
                            key=tuple(np.round(cn * 2000).astype(int)), cd=float(np.dot(cn, p)),
                            corners=np.array([p - e1 - e2, p + e1 - e2, p + e1 + e2, p - e1 + e2])))
        return out

    # ------------------------------------------------ hidden faces
    def _aabb(self, c):
        R, C = np.asarray(c.axes, float), np.asarray(c.center, float)
        h = np.abs(R) @ (np.asarray(c.size, float) / 2)
        return C - h, C + h

    def cull(self):
        cubes = self.cubes()
        for c in cubes:
            c.faces = dict(c.orig)
        grid = {}
        boxes = {}
        for c in cubes:
            lo, hi = self._aabb(c)
            boxes[id(c)] = (lo, hi, np.allclose(np.abs(np.asarray(c.axes, float)), EYE, atol=1e-9))
            for gx in range(int(math.floor(lo[0])), int(math.floor(hi[0])) + 1):
                for gy in range(int(math.floor(lo[1])), int(math.floor(hi[1])) + 1):
                    for gz in range(int(math.floor(lo[2])), int(math.floor(hi[2])) + 1):
                        grid.setdefault((gx, gy, gz), []).append(c)
        n_cut = 0
        for c in cubes:
            for f in self._faces(c, 0.0):
                if f["n"][1] < -0.999 and f["centre"][1] < 1e-4:
                    c.faces[f["bb"]] = None          # on the ground
                    n_cut += 1
                    continue
                if self._hidden(c, f, grid, boxes):
                    c.faces[f["bb"]] = None
                    n_cut += 1
        return n_cut

    def _hidden(self, c, f, grid, boxes):
        cs = f["corners"]
        lo, hi = cs.min(0), cs.max(0)
        cand = set()
        out = []
        for gx in range(int(math.floor(lo[0] - 1e-3)), int(math.floor(hi[0] + 1e-3)) + 1):
            for gy in range(int(math.floor(lo[1] - 1e-3)), int(math.floor(hi[1] + 1e-3)) + 1):
                for gz in range(int(math.floor(lo[2] - 1e-3)), int(math.floor(hi[2] + 1e-3)) + 1):
                    for o in grid.get((gx, gy, gz), ()):
                        if o is c or id(o) in cand:
                            continue
                        cand.add(id(o))
                        if self.coverer_ok(c.group, o.group):
                            out.append(o)
        if not out:
            return False
        n = f["n"]
        kk = int(np.argmax(np.abs(n)))
        aligned = boxes[id(c)][2] and abs(abs(n[kk]) - 1) < 1e-9
        if aligned and all(boxes[id(o)][2] for o in out):
            s = 1 if n[kk] > 0 else -1
            q = f["centre"][kk] + s * 1e-4
            a, b = [j for j in range(3) if j != kk]
            a0, a1, b0, b1 = lo[a], hi[a], lo[b], hi[b]
            rects = []
            for o in out:
                olo, ohi, _ = boxes[id(o)]
                if not (olo[kk] < q < ohi[kk]):
                    continue
                r = (max(a0, olo[a]), min(a1, ohi[a]), max(b0, olo[b]), min(b1, ohi[b]))
                if r[1] - r[0] > 1e-7 and r[3] - r[2] > 1e-7:
                    rects.append(r)
            if not rects:
                return False
            xs = sorted({a0, a1} | {r[0] for r in rects} | {r[1] for r in rects})
            ys = sorted({b0, b1} | {r[2] for r in rects} | {r[3] for r in rects})
            for i in range(len(xs) - 1):
                xm = (xs[i] + xs[i + 1]) / 2
                if xs[i + 1] - xs[i] < 1e-7:
                    continue
                for j in range(len(ys) - 1):
                    if ys[j + 1] - ys[j] < 1e-7:
                        continue
                    ym = (ys[j] + ys[j + 1]) / 2
                    if not any(r[0] <= xm <= r[1] and r[2] <= ym <= r[3] for r in rects):
                        return False
            return True
        # sampled test (turned cubes)
        pts = [cs[0] * (1 - u) * (1 - v) + cs[1] * u * (1 - v) + cs[2] * u * v + cs[3] * (1 - u) * v
               for u in np.linspace(0.005, 0.995, 9) for v in np.linspace(0.005, 0.995, 9)]
        pts = np.array(pts) + n * 1e-4
        inside = np.zeros(len(pts), bool)
        for o in out:
            R, C = np.asarray(o.axes, float), np.asarray(o.center, float)
            h = np.asarray(o.size, float) / 2
            loc = (pts - C) @ R
            inside |= np.all(np.abs(loc) < h - 1e-7, axis=1)
            if inside.all():
                return True
        return False

    # ------------------------------------------------ coplanar / near faces
    def _all_faces(self, ang):
        out = []
        for c in self.cubes():
            out.extend(self._faces(c, ang))
        return out

    def pairs(self, ang):
        faces = self._all_faces(ang)
        buckets = {}
        for f in faces:
            buckets.setdefault(f["key"], []).append(f)
        out = []
        for lst in buckets.values():
            lst.sort(key=lambda f: f["cd"])
            for i in range(len(lst)):
                f = lst[i]
                for j in range(i + 1, len(lst)):
                    g = lst[j]
                    if g["cd"] - f["cd"] >= MIN_GAP - 1e-6:
                        break
                    if g["cube"] is f["cube"] or not self.compatible(f["cube"].group, g["cube"].group):
                        continue
                    if abs(float(np.dot(f["n"], g["n"]))) < 0.99999:
                        continue
                    if DA.overlap(f, g):
                        out.append((f, g))
        return out

    def _conflicts(self, c, center, size, index):
        n = 0
        for ang, idx in index.items():
            for f in self._faces(c, ang, center, size):
                ent = idx.get(f["key"])
                if not ent:
                    continue
                for g in ent:
                    if g["cube"] is c or abs(g["cd"] - f["cd"]) >= MIN_GAP - 1e-6:
                        continue
                    if not self.compatible(c.group, g["cube"].group) or abs(float(np.dot(f["n"], g["n"]))) < 0.99999:
                        continue
                    if DA.overlap(f, g):
                        n += 1
        return n

    def resolve(self, passes=30, verbose=True):
        for c in self.cubes():
            c.group = self.group_of(c.bone)
            b = c.bone
            while b is not None and not b.name.startswith("gear_"):
                b = b.parent
            c.gbone = b
        angs = (0.0, 45.0)
        stats = {"moved": 0, "stuck": 0}
        for it in range(passes):
            ncut = self.cull()
            prs = []
            for a in angs:
                prs += self.pairs(a)
            if verbose:
                print("  resolve pass %d: culled %d faces, %d pairs" % (it + 1, ncut, len(prs)), flush=True)
            if not prs:
                break
            index = {}
            for a in angs:
                idx = {}
                for f in self._all_faces(a):
                    idx.setdefault(f["key"], []).append(f)
                index[a] = idx
            moved = set()
            stuck = 0
            for f, g in prs:
                if id(f["cube"]) in moved or id(g["cube"]) in moved:
                    continue
                done = False
                opp = float(np.dot(f["n"], g["n"])) < 0
                order = sorted((f, g), key=lambda x: (x["cube"].group[0] == "static", x["area"]))
                for w, o in ((order[0], order[1]), (order[1], order[0])):
                    c = w["cube"]
                    sigma = float(np.dot(w["centre"] - o["centre"], w["n"]))
                    grow, shrink = STEP - sigma, -STEP - sigma
                    cands = [grow, grow + STEP] if opp else [grow, shrink, grow + STEP, shrink - STEP]
                    if opp:
                        cands += [shrink]
                    before = self._conflicts(c, c.center, c.size, index)
                    best = None
                    for m in cands:
                        size = np.asarray(c.size, float).copy()
                        if size[w["k"]] + m < 2 * MIN_GAP:
                            continue
                        size[w["k"]] += m
                        ax = np.asarray(c.axes, float)[:, w["k"]]
                        center = np.asarray(c.center, float) + ax * w["s"] * m / 2
                        after = self._conflicts(c, center, size, index)
                        if after < before and (best is None or after < best[0]):
                            best = (after, center, size)
                            if after == 0:
                                break
                    if best is not None:
                        c.center, c.size = best[1], best[2]
                        moved.add(id(c))
                        stats["moved"] += 1
                        done = True
                        break
                if not done:
                    stuck += 1
            stats["stuck"] = stuck
            if not moved:
                break
        return stats

    # ------------------------------------------------ uv
    def _uv(self, c, bb, spec):
        if isinstance(spec, tuple) and spec[0] == "pic":
            r = self.regions[spec[1]]
            if len(spec) > 2:
                s0, t0, s1, t1 = spec[2]
                return [r[0] + s0 * r[2], r[1] + t0 * r[3], r[0] + s1 * r[2], r[1] + t1 * r[3]]
            return [r[0], r[1], r[0] + r[2], r[1] + r[3]]
        band = isinstance(spec, tuple) and spec[0] == "band"
        name = spec[1] if band else spec
        r = self.regions[name]
        size = np.asarray(c.size, float)
        aligned = np.allclose(np.asarray(c.axes, float), EYE, atol=1e-9)
        C = np.asarray(c.center, float)
        if aligned:
            lo, hi = C - size / 2, C + size / 2
        else:
            seed = zlib.crc32(c.name.encode()) % 97
            lo, hi = -size / 2 + seed * 0.37, size / 2 + seed * 0.37
        a0, b0, du, dv = {
            "north": (lo[0], -hi[1], size[0], size[1]), "south": (-hi[0], -hi[1], size[0], size[1]),
            "west": (-hi[2], -hi[1], size[2], size[1]), "east": (lo[2], -hi[1], size[2], size[1]),
            "up": (-hi[0], -hi[2], size[0], size[2]), "down": (-hi[0], lo[2], size[0], size[2])}[bb]
        su, sv = du * 16, dv * 16
        if band:
            if name.endswith("_u"):
                sv = r[3]
                b0 = 0
            else:
                su = r[2]
                a0 = 0
        su, sv = min(su, r[2]), min(sv, r[3])
        u0 = (a0 * 16) % r[2]
        v0 = (b0 * 16) % r[3]
        if u0 + su > r[2] + 1e-6:
            u0 = r[2] - su
        if v0 + sv > r[3] + 1e-6:
            v0 = r[3] - sv
        return [r[0] + u0, r[1] + v0, r[0] + u0 + su, r[1] + v0 + sv]

    # ------------------------------------------------ export
    def texture_png(self):
        a = np.clip(self.atlas.arr, 0, 255).astype(np.uint8)
        a[..., 3] = 255
        return Image.fromarray(a, "RGBA")

    def to_model(self, tex_rel, png):
        elements = []

        def group_json(b):
            children = []
            for c in b.cubes:
                Rbb = gg.to_bb_rot(np.asarray(c.axes, float))
                euler = gg.matrix_to_euler_zyx(Rbb)
                center = gg.to_bb_point(np.asarray(c.center, float))
                half = np.asarray(c.size, float) * 8.0
                frm = [round(center[k] - half[k], 4) for k in range(3)]
                to = [round(center[k] + half[k], 4) for k in range(3)]
                faces = {}
                for bb in ("north", "east", "south", "west", "up", "down"):
                    spec = c.faces.get(bb)
                    if spec is None:
                        faces[bb] = {"uv": [0, 0, 0, 0], "texture": None}
                    else:
                        faces[bb] = {"uv": [round(float(x), 4) for x in self._uv(c, bb, spec)], "texture": 0}
                el = {"name": c.name, "box_uv": False, "rescale": False, "locked": False, "render_order": "default",
                      "allow_mirror_modeling": True, "from": frm, "to": to, "autouv": 0, "color": 0,
                      "origin": center, "faces": faces, "type": "cube", "uuid": c.uuid}
                if any(abs(x) > 1e-4 for x in euler):
                    el["rotation"] = euler
                elements.append(el)
                children.append(c.uuid)
            for ch in b.children:
                children.append(group_json(ch))
            return {"name": b.name, "origin": gg.to_bb_point(b.origin), "color": 0, "uuid": b.uuid, "export": True,
                    "mirror_uv": False, "isOpen": False, "locked": False, "visibility": True, "autouv": 0,
                    "children": children}
        outliner = [group_json(self.root)]
        tex = gn.texture_entry(tex_rel, self.size, png, "entity", tex_rel)
        tex["id"] = "0"
        return {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": self.name,
                "model_identifier": self.name, "visible_box": [13, 10, 0], "variable_placeholders": "",
                "variable_placeholder_buttons": [], "timeline_setups": [], "unhandled_root_fields": {},
                "resolution": {"width": self.size, "height": self.size}, "elements": elements,
                "outliner": outliner, "textures": [tex], "animations": []}

    def export(self, descriptor=None, icon=None, verbose=True):
        st = self.resolve(verbose=verbose)
        print("resolve:", st)
        tex_rel = "%s.png" % self.name
        tex_path = os.path.join(ASSETS, "textures/entity", tex_rel)
        os.makedirs(os.path.dirname(tex_path), exist_ok=True)
        self.texture_png().save(tex_path, optimize=True)
        with open(tex_path, "rb") as f:
            png = f.read()
        model = self.to_model(tex_rel, png)
        for p, compact in ((os.path.join(ROOT, "blockbench/%s.bbmodel" % self.name), False),
                           (os.path.join(ASSETS, "models/entity/%s.bbmodel" % self.name), True)):
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w") as f:
                gn.json_dump(model, f, compact)
        if descriptor is not None:
            p = os.path.join(ASSETS, "workshops/%s.json" % self.name)
            with open(p, "w") as f:
                json.dump(descriptor, f, indent=1)
        self.model = model
        print("%s: %d cubes, texture %dx%d" % (self.name, len(model["elements"]), self.size, self.size))
        return model


# ---------------------------------------------------------------- renders
def quads_of(model, frame=0, craft=True, gear_angle=0.0, hide=()):
    import forge_audit as FA
    m = FA.posed(model, gear_angle)
    fam = FA.families(model)
    sel = {f: v[frame % len(v)] for f, v in fam.items()}
    out = []
    for f in DA.faces_of(m):
        if not FA.visible(f["chain"], sel, "craft" if craft else "none"):
            continue
        if any(h in f["chain"] for h in hide):
            continue
        out.append((f["corners"], f["uvs"], f["glow"], 0))
    return out


def render(quads, tex, W, H, eye, target, fov=None, ortho=None, bg=(52, 50, 54)):
    return dl.render(quads, np.asarray(tex).astype(float), W, H, eye, target, fov=fov, ortho=ortho, bg=bg)


# the reference camera (fitted on the picture: 1536 x 1024, slightly plunging front view)
REF_CAM = dict(eye=(0.0, 13.5, 33.0), target=(0.0, 4.15, 0.0), fov=20.5)


def sheet(model, tex, out, title="", frame=0, extra_quads=None, extra_tex=None):
    q = quads_of(model, frame)
    views = []
    W, H = 768, 512
    ref = Image.open(REF).convert("RGB").resize((W, H), Image.LANCZOS)
    views.append(("reference", ref))
    views.append(("face (camera ref)", render(q, tex, W, H, **REF_CAM)))
    views.append(("3/4 avant gauche", render(q, tex, W, H, eye=(-17, 10, 21), target=(0, 3.8, 0), fov=30)))
    views.append(("dos", render(q, tex, W, H, eye=(9, 9, -26), target=(0, 3.8, 0), fov=28)))
    views.append(("dessus", render(q, tex, W, H, eye=(0.01, 34, 6), target=(0, 0, 0.2), fov=26)))
    views.append(("face ortho", render(q, tex, W, H, eye=(0, 4.8, 60), target=(0, 4.8, 0), ortho=7.2)))
    cols = 2
    rows = (len(views) + 1) // 2
    sh = Image.new("RGB", (cols * (W + 8), rows * (H + 26) + 30), (24, 24, 28))
    dr = ImageDraw.Draw(sh)
    dr.text((8, 8), title, fill=(240, 230, 200))
    for k, (t, im) in enumerate(views):
        x, y = (k % cols) * (W + 8), 30 + (k // cols) * (H + 26)
        sh.paste(im, (x, y + 20))
        dr.text((x + 6, y + 4), t, fill=(235, 225, 200))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    sh.save(out)
    print("sheet:", out)
    return views
