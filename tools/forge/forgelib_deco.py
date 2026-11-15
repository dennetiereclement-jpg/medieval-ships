"""Bibliotheque du modele DECOR de la Forge divine (1.34.0) : statue ailee, aureole, bannieres, chaines, lanternes,
tableau de plans, outils, cristal, presse. Utilisee par tools/forge/generate_forge_divine_deco.py, auditee par
tools/forge/forge_audit_deco.py.

    import forgelib_deco as fd
    m = fd.Model("forge_divine_deco")            # son propre atlas (512 px), os racine "deco"
    b = m.bone("statue", parent=m.root, pivot=(0, 6.5, -0.5))
    m.box(b, "socle", x0, y0, z0, x1, y1, z1, "stone")      # boite alignee, coordonnees en BLOCS
    m.box(b, "glow_croix", ..., "glow_gold")     # nom glow* : pleine lumiere (le rendu Java)
    m.box(b, "vitre", ..., {"all": "iron", "+z": ("lantern_glass", "stretch")})
    m.resolve(fixed=faces_de_la_structure)       # faces cachees retirees, aucune paire coplanaire / parallele < 1/64
    m.export()                                   # bbmodel (models/entity + blockbench) + texture

REPERE : blocs, origine = centre du bloc d'ancrage, y = 0 = dessus du sol, +z = face AVANT, +x = droite vue de face.
Toutes les boites sont alignees sur les axes (pixel art Minecraft). Les materiaux "tile" sont des tuiles 64 px
plaquees a 16 px par bloc, alignees sur le monde (les boites voisines se raccordent) ; "stretch" etire une image
entiere sur la face (vitres, maillons, plans).

RESOLUTION (zero defaut) : resolve() retire chaque face entierement cachee dans une boite statique voisine (contact
ou interieur), puis ecarte toute paire de faces paralleles qui se recouvrent a moins de 1/64 bloc en deplacant une
face de 1/32 le long de sa normale (le deplacement qui cree le moins de nouveaux conflits). Les boites des os craft_*
ne cachent jamais rien (elles disparaissent au repos). Les faces de la structure (agent A) sont des obstacles fixes.
"""
import base64
import json
import math
import os
import random
import uuid as _uuid

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
ASSETS = os.path.join(ROOT, "src/main/resources/assets/medievalships")
SCRATCH = "/tmp/claude-0/-home-user-medieval-ships/2a9b6be4-7c0a-5b40-ad8d-40cfe82b9e67/scratchpad"
TEX = 512
T = 64                 # cote d'une tuile de materiau (px)
PPB = 16               # px par bloc sur les faces
MIN_GAP = 1.0 / 64
STEP = 1.0 / 32        # deplacement du resolveur
MIN_TH = 1.0 / 32      # epaisseur minimale d'une boite
FACE_BB = {"+z": "north", "-z": "south", "+x": "west", "-x": "east", "+y": "up", "-y": "down"}
KEYS = ("+x", "-x", "+y", "-y", "+z", "-z")


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def mix(a, b, t):
    return tuple(int(round(a[k] + (b[k] - a[k]) * t)) for k in range(3))


def shade(c, k):
    return tuple(max(0, min(255, int(round(v * k)))) for v in c[:3])


# ---------------------------------------------------------------- palette (relevee sur forge.png)
GOLD, GOLD_L, GOLD_D = rgb("d89e2e"), rgb("ffd870"), rgb("8a5816")
BRONZE, BRONZE_L, BRONZE_D = rgb("a86c2a"), rgb("d8a050"), rgb("5a3410")
STONE, STONE_L, STONE_D = rgb("7a7472"), rgb("a29c98"), rgb("45403f")
DSTONE = rgb("4e4848")
IRON, IRON_L, IRON_D = rgb("3c383c"), rgb("6e666a"), rgb("1c1a1c")
WOOD, WOOD_L, WOOD_D = rgb("8c5428"), rgb("b8743a"), rgb("4c2c12")
WOODG, WOODG_L, WOODG_D = rgb("c48e40"), rgb("e8bc66"), rgb("7a5220")
FEATH, FEATH_L, FEATH_D = rgb("e6dccb"), rgb("fbf6ec"), rgb("b4a48c")
FEATH2 = rgb("d4c6ae")
ROBE, ROBE_L = rgb("f2e8d2"), rgb("fffaf0")
NAVY, NAVY_L, NAVY_D = rgb("283050"), rgb("3c4670"), rgb("181e38")
BLUEP, BLUEP_L = rgb("24407a"), rgb("c8d6ea")


class Painter:
    """Peint dans le tableau RGBA de l'atlas, dans le rectangle (u0, v0, w, h)."""

    def __init__(self, arr, u0, v0, w, h, seed):
        self.a, self.u0, self.v0, self.w, self.h = arr, u0, v0, w, h
        self.rng = random.Random(seed)

    def put(self, i, j, c):
        i, j = int(i), int(j)
        if 0 <= i < self.w and 0 <= j < self.h:
            self.a[self.v0 + j, self.u0 + i] = (c[0], c[1], c[2], 255)

    def get(self, i, j):
        return tuple(int(v) for v in self.a[self.v0 + j, self.u0 + i, :3])

    def jit(self, c, n):
        d = self.rng.randint(-n, n) if n else 0
        return tuple(max(0, min(255, v + d)) for v in c)

    def rect(self, i0, i1, j0, j1, c, noise=0):
        for j in range(int(j0), int(j1)):
            for i in range(int(i0), int(i1)):
                self.put(i, j, self.jit(c, noise))

    def cells(self, base, light, dark, cw=2, ch=2, noise=10, hi=0.35, lo=0.30, rows_offset=False):
        """Pixel art en voxels : cellules cw x ch, ton propre, arete haute/gauche eclairee, basse assombrie."""
        for cj in range(0, self.h, ch):
            off = (cw // 2) if rows_offset and (cj // ch) % 2 else 0
            for ci in range(-off, self.w, cw):
                tone = self.jit(base, noise)
                for dj in range(ch):
                    for di in range(cw):
                        c = tone
                        if dj == 0:
                            c = mix(c, light, hi)
                        elif di == 0:
                            c = mix(c, light, hi * 0.5)
                        if dj == ch - 1 and ch > 1:
                            c = mix(c, dark, lo)
                        self.put(ci + di, cj + dj, self.jit(c, 3))

    def feathers(self, base, light, dark, ch=4, noise=8):
        """Plumes en voxels de 1/8 bloc : colonnes de 2 px (bord gauche clair, droit ombre), ecailles decalees de
        ch px d'une colonne a l'autre, pointe sombre en bas de chaque ecaille."""
        for ci in range(0, self.w, 2):
            off = (ci // 2 % 2) * (ch // 2)
            for cj in range(-ch, self.h, ch):
                tone = self.jit(base, noise)
                for dj in range(ch):
                    for di in range(2):
                        c = mix(tone, light, 0.45) if di == 0 else tone
                        if dj == 0:
                            c = mix(c, light, 0.35)
                        if dj == ch - 1:
                            c = mix(c, dark, 0.55 if di else 0.35)
                        self.put(ci + di, cj + dj + off, self.jit(c, 2))

    def bricks(self, base, mortar, light, bw=8, bh=4, noise=10):
        for j in range(self.h):
            row = j // bh
            for i in range(self.w):
                ii = i + (bw // 2 if row % 2 else 0)
                if j % bh == bh - 1 or ii % bw == bw - 1:
                    c = mortar
                else:
                    c = base
                    if j % bh == 0:
                        c = mix(c, light, 0.25)
                self.put(i, j, c)
        for r in range(0, self.h, bh):
            for b0 in range(-bw, self.w, bw):
                off = bw // 2 if (r // bh) % 2 else 0
                d = self.rng.randint(-noise, noise)
                for j in range(r, min(self.h, r + bh - 1)):
                    for i in range(b0 - off, b0 - off + bw - 1):
                        if 0 <= i < self.w:
                            c = self.get(i, j)
                            self.put(i, j, self.jit(tuple(max(0, min(255, v + d)) for v in c), 4))

    def planks(self, base, dark, light, ph=4, noise=8):
        for j0 in range(0, self.h, ph):
            tone = self.jit(base, noise)
            ph_ = [self.rng.uniform(0, 6.3) for _ in range(2)]
            for dj in range(ph):
                for i in range(self.w):
                    if dj == ph - 1:
                        c = dark
                    elif dj == 0:
                        c = mix(tone, light, 0.3)
                    else:
                        k = 1.0 + 0.06 * math.sin(i * 0.4 + ph_[0]) - (0.1 if abs(dj - 1.5 - 0.8 * math.sin(i * 0.23 + ph_[1])) < 0.4 else 0)
                        c = shade(tone, k)
                    self.put(i, j0 + dj, self.jit(c, 3))


# ---------------------------------------------------------------- tuiles et images
def tile_cells(base, light, dark, cw=2, ch=2, noise=10, hi=0.35, lo=0.3, off=False):
    return lambda p: p.cells(base, light, dark, cw, ch, noise, hi, lo, off)


def tile_flat(c, noise=6):
    return lambda p: p.rect(0, p.w, 0, p.h, c, noise)


def pic_link(p):
    """Maillon de chaine vu de face : cadre fer eclaire, trou sombre."""
    p.rect(0, p.w, 0, p.h, IRON)
    for i in range(p.w):
        p.put(i, 0, IRON_L)
        p.put(i, p.h - 1, IRON_D)
    for j in range(p.h):
        p.put(0, j, mix(IRON, IRON_L, 0.6))
        p.put(p.w - 1, j, IRON_D)
    p.rect(1, p.w - 1, 2, p.h - 2, rgb("141214"))


def pic_lantern(p):
    """Vitre de lanterne allumee : verre orange, coeur clair, croisillon bronze."""
    w, h = p.w, p.h
    for j in range(h):
        for i in range(w):
            d = math.hypot((i + 0.5 - w / 2) / (w / 2), (j + 0.5 - h / 2) / (h / 2))
            c = mix(rgb("fff0b0"), rgb("ff9a2a"), min(1, d * 0.95))
            p.put(i, j, p.jit(c, 6))
    for j in range(h):
        p.put(w // 2, j, rgb("a8601e"))
        p.put(w // 2 - 1, j, rgb("c07428"))
    for i in range(w):
        p.put(i, h // 2, rgb("a8601e"))
    for i in range(w):
        p.put(i, 0, rgb("6a3c14"))
        p.put(i, h - 1, rgb("6a3c14"))
    for j in range(h):
        p.put(0, j, rgb("6a3c14"))
        p.put(w - 1, j, rgb("6a3c14"))


def pic_blueprint(p):
    """Plan technique bleu : quadrillage, engrenage dessine au trait clair, annotations."""
    w, h = p.w, p.h
    p.rect(0, w, 0, h, BLUEP, 5)
    for j in range(h):
        for i in range(w):
            if i % 8 == 0 or j % 8 == 0:
                p.put(i, j, mix(BLUEP, BLUEP_L, 0.18))
    cx, cy = w / 2, h / 2 + 1
    R0, R1 = h * 0.30, h * 0.20
    for j in range(h):
        for i in range(w):
            x, y = i + 0.5 - cx, j + 0.5 - cy
            r = math.hypot(x, y)
            a = math.atan2(y, x)
            tooth = (math.cos(a * 8) > 0.35)
            line = abs(r - R0) < 0.9 or (tooth and R0 <= r <= R0 + 4.5 and (abs(r - R0 - 4) < 0.8 or
                                                                              abs(math.cos(a * 8) - 0.35) < 0.18))
            line = line or abs(r - R1) < 0.8 or abs(r - 3.2) < 0.8
            if not line and R1 < r < R0:
                for k in range(4):
                    ang = k * math.pi / 2 + math.pi / 4
                    if abs(-x * math.sin(ang) + y * math.cos(ang)) < 0.8 and (x * math.cos(ang) + y * math.sin(ang)) > 0:
                        line = True
            if line:
                p.put(i, j, BLUEP_L)
    for (i0, j0) in ((3, 3), (w - 9, 3), (3, h - 6), (w - 10, h - 6)):
        for k in range(6):
            if p.rng.random() < 0.7:
                p.put(i0 + k, j0, BLUEP_L)
            if p.rng.random() < 0.5:
                p.put(i0 + k, j0 + 2, mix(BLUEP, BLUEP_L, 0.7))
    for i in range(w):
        p.put(i, 0, rgb("162a52"))
        p.put(i, h - 1, rgb("162a52"))
    for j in range(h):
        p.put(0, j, rgb("162a52"))
        p.put(w - 1, j, rgb("162a52"))


def pic_crystal(p):
    w, h = p.w, p.h
    for j in range(h):
        for i in range(w):
            t = abs(i + 0.5 - w / 2) / (w / 2)
            c = mix(rgb("fff6c8"), rgb("f6b83a"), t * 0.9)
            if (i + j) % 7 == 0:
                c = mix(c, rgb("ffffff"), 0.4)
            p.put(i, j, p.jit(c, 5))


def pic_holy(p):
    w, h = p.w, p.h
    for j in range(h):
        for i in range(w):
            t = abs(i + 0.5 - w / 2) / (w / 2)
            p.put(i, j, p.jit(mix(rgb("fffbe0"), rgb("ffd468"), t), 4))


MATERIALS = {
    "gold": (T, T, tile_cells(GOLD, GOLD_L, GOLD_D, 2, 2, 12)),
    "gold_l": (T, T, tile_cells(mix(GOLD, GOLD_L, 0.45), GOLD_L, GOLD, 2, 2, 10)),
    "bronze": (T, T, tile_cells(BRONZE, BRONZE_L, BRONZE_D, 2, 2, 10)),
    "stone": (T, T, lambda p: p.bricks(STONE, STONE_D, STONE_L, 8, 4, 12)),
    "stone_d": (T, T, lambda p: p.bricks(DSTONE, rgb("2c2828"), STONE, 8, 4, 8)),
    "iron": (T, T, tile_cells(IRON, IRON_L, IRON_D, 2, 2, 6)),
    "wood": (T, T, lambda p: p.planks(WOOD, WOOD_D, WOOD_L, 4)),
    "wood_d": (T, T, lambda p: p.planks(WOOD_D, rgb("2c1808"), WOOD, 4)),
    "woodg": (T, T, lambda p: p.planks(WOODG, WOODG_D, WOODG_L, 4)),
    "feather": (T, T, lambda p: p.feathers(FEATH, FEATH_L, FEATH_D, 4, 8)),
    "feather2": (T, T, lambda p: p.feathers(FEATH2, FEATH, rgb("9c8a70"), 6, 8)),
    "feather_l": (T, T, lambda p: p.feathers(mix(FEATH, FEATH_L, 0.6), FEATH_L, FEATH, 3, 5)),
    "robe": (T, T, tile_cells(ROBE, ROBE_L, rgb("d8c8a6"), 2, 2, 6, 0.3, 0.25)),
    "navy": (T, T, tile_cells(NAVY, NAVY_L, NAVY_D, 2, 2, 5, 0.2, 0.25)),
    "glow_gold": (T, T, tile_cells(rgb("ffc850"), rgb("fff2b0"), rgb("e89a28"), 2, 2, 8, 0.4, 0.2)),
    "glow_white": (32, 32, pic_holy),
    "lantern_glass": (16, 20, pic_lantern),
    "link": (4, 8, pic_link),
    "blueprint": (64, 56, pic_blueprint),
    "crystal": (16, 32, pic_crystal),
}


class Atlas:
    def __init__(self, size=TEX):
        self.size = size
        self.arr = np.zeros((size, size, 4), np.uint8)
        self.arr[..., 3] = 255
        self.regions = {}
        self.x = self.y = self.row_h = 0
        for i, (name, (w, h, painter)) in enumerate(MATERIALS.items()):
            self.add(name, w, h, painter, seed=17 + i * 31)

    def add(self, name, w, h, painter, seed=1):
        if self.x + w > self.size:
            self.x, self.y, self.row_h = 0, self.y + self.row_h, 0
        if self.y + h > self.size:
            raise ValueError("atlas plein")
        self.regions[name] = (self.x, self.y, w, h)
        painter(Painter(self.arr, self.x, self.y, w, h, seed))
        self.x += w
        self.row_h = max(self.row_h, h)

    def png(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        Image.fromarray(self.arr, "RGBA").save(path)
        with open(path, "rb") as f:
            return f.read()


# ---------------------------------------------------------------- modele
class Bone:
    def __init__(self, name, pivot=(0, 0, 0), parent=None):
        self.name, self.pivot, self.parent = name, tuple(float(v) for v in pivot), parent
        self.children, self.boxes = [], []
        if parent:
            parent.children.append(self)

    def craft(self):
        b = self
        while b:
            if b.name.startswith("craft_"):
                return True
            b = b.parent
        return False


class Box:
    def __init__(self, bone, name, lo, hi, faces):
        self.bone, self.name = bone, name
        self.lo, self.hi = np.array(lo, float), np.array(hi, float)
        self.faces = faces          # key -> (material, mode) or None
        self.culled = set()
        self.cover = not bone.craft()

    def size(self):
        return self.hi - self.lo


def _axis(key):
    return "xyz".index(key[1]), (1 if key[0] == "+" else -1)


class Model:
    def __init__(self, name):
        self.name = name
        self.atlas = Atlas()
        self.root = Bone("deco")
        self.boxes = []
        self._uid = 0

    def bone(self, name, parent=None, pivot=(0, 0, 0)):
        return Bone(name, pivot, parent or self.root)

    def box(self, bone, name, x0, y0, z0, x1, y1, z1, mat, **kw):
        lo = (min(x0, x1), min(y0, y1), min(z0, z1))
        hi = (max(x0, x1), max(y0, y1), max(z0, z1))
        if min(hi[k] - lo[k] for k in range(3)) < MIN_TH - 1e-9:
            raise ValueError("%s trop fin: %s %s" % (name, lo, hi))
        if isinstance(mat, str):
            mat = {"all": mat}
        faces = {}
        for k in KEYS:
            m = mat.get(k, mat.get("all"))
            if m is None:
                faces[k] = None
            elif isinstance(m, tuple):
                faces[k] = m
            else:
                faces[k] = (m, "stretch" if MATERIALS[m][0] < T or m in ("blueprint", "glow_white") else "tile")
        b = Box(bone, name, lo, hi, faces)
        bone.boxes.append(b)
        self.boxes.append(b)
        return b

    def cbox(self, bone, name, c, s, mat):
        """Boite par centre (cx, cy, cz) et tailles (sx, sy, sz)."""
        return self.box(bone, name, c[0] - s[0] / 2, c[1] - s[1] / 2, c[2] - s[2] / 2,
                        c[0] + s[0] / 2, c[1] + s[1] / 2, c[2] + s[2] / 2, mat)

    def empty(self, name, pivot, parent=None):
        return Bone(name, pivot, parent or self.root)

    # ------------------------------------------------------------ faces
    def face_list(self, boxes=None, drawn_only=True):
        out = []
        for b in (self.boxes if boxes is None else boxes):
            for key in KEYS:
                if drawn_only and (b.faces[key] is None or key in b.culled):
                    continue
                k, s = _axis(key)
                o = [j for j in range(3) if j != k]
                p = b.hi[k] if s > 0 else b.lo[k]
                out.append((k, s, p, b.lo[o[0]], b.hi[o[0]], b.lo[o[1]], b.hi[o[1]], b, key))
        return out

    def _cull(self):
        """Retire les faces entierement contenues dans le volume ferme d'une autre boite statique."""
        n = 0
        cov = [b for b in self.boxes if b.cover]
        grid = {}
        for b in cov:
            for gx in range(int(math.floor(b.lo[0])), int(math.floor(b.hi[0])) + 1):
                for gy in range(int(math.floor(b.lo[1])), int(math.floor(b.hi[1])) + 1):
                    grid.setdefault((gx, gy), []).append(b)
        e = 1e-7
        for b in self.boxes:
            b.culled = set()
            for key in KEYS:
                if b.faces[key] is None:
                    continue
                k, s = _axis(key)
                o = [j for j in range(3) if j != k]
                p = b.hi[k] if s > 0 else b.lo[k]
                lo, hi = b.lo.copy(), b.hi.copy()
                lo[k] = hi[k] = p
                cands = set()
                for gx in range(int(math.floor(lo[0])), int(math.floor(hi[0])) + 1):
                    for gy in range(int(math.floor(lo[1])), int(math.floor(hi[1])) + 1):
                        cands.update(id(c) for c in grid.get((gx, gy), ()))
                for c in cov:
                    if id(c) not in cands or c is b:
                        continue
                    if all(c.lo[j] - e <= lo[j] and hi[j] <= c.hi[j] + e for j in range(3)):
                        b.culled.add(key)
                        n += 1
                        break
        return n

    @staticmethod
    def _conflicts(fs_a, fs_b, same=False):
        """Paires (fa, fb) de faces paralleles (meme axe) a moins de 1/64 qui se recouvrent."""
        buckets = {}
        for f in fs_b:
            buckets.setdefault((f[0], int(math.floor(f[2] * 64))), []).append(f)
        out = []
        for fa in fs_a:
            for d in (-1, 0, 1):
                for fb in buckets.get((fa[0], int(math.floor(fa[2] * 64)) + d), ()):
                    if fb[7] is fa[7] or (same and id(fb) <= id(fa)):
                        continue
                    if abs(fa[2] - fb[2]) >= MIN_GAP - 1e-7:
                        continue
                    if min(fa[4], fb[4]) - max(fa[3], fb[3]) > 1e-6 and min(fa[6], fb[6]) - max(fa[5], fb[5]) > 1e-6:
                        out.append((fa, fb))
        return out

    @staticmethod
    def _count(fs, buckets, exclude):
        n = 0
        for fa in fs:
            for d in (-1, 0, 1):
                for fb in buckets.get((fa[0], int(math.floor(fa[2] * 64)) + d), ()):
                    if fb[7] is exclude or abs(fa[2] - fb[2]) >= MIN_GAP - 1e-7:
                        continue
                    if min(fa[4], fb[4]) - max(fa[3], fb[3]) > 1e-6 and min(fa[6], fb[6]) - max(fa[5], fb[5]) > 1e-6:
                        n += 1
        return n

    def resolve(self, fixed=(), passes=60, verbose=True):
        """fixed: faces de la structure (k, s, p, a0, a1, b0, b1, None, nom) qu'on ne deplace jamais."""
        fixed = list(fixed)
        moved = 0
        self._moves = {}
        for it in range(passes):
            self._cull()
            mine = self.face_list()
            pairs = self._conflicts(mine, mine, same=True) + self._conflicts(mine, fixed)
            if verbose:
                print("  resolve passe %d: %d paires" % (it + 1, len(pairs)), flush=True)
            if not pairs:
                return moved
            touched = set()
            buckets = {}
            for f in mine + fixed:
                buckets.setdefault((f[0], int(math.floor(f[2] * 64))), []).append(f)
            H = 1.0 / 64
            for fa, fb in pairs:
                if id(fa[7]) in touched or (fb[7] is not None and id(fb[7]) in touched):
                    continue
                best = None
                for f, g in ((fa, fb), (fb, fa)):
                    b = f[7]
                    if b is None:
                        continue
                    k, s = f[0], f[1]
                    # une face en contact avec une autre boite ne recule jamais (pas de fente ouverte)
                    contact = any(c[7] is not b and c[1] == -s and abs(c[2] - f[2]) < 1e-6
                                  and min(f[4], c[4]) - max(f[3], c[3]) > 1e-6 and min(f[6], c[6]) - max(f[5], c[5]) > 1e-6
                                  for dd in (-1, 0, 1) for c in buckets.get((k, int(math.floor(f[2] * 64)) + dd), ()))
                    for d in (1, -1, 1.5, -1.5, 2, -2, 3, -3, 4, -4):
                        target = g[2] + d * H
                        if abs(target - f[2]) > 5 * H:
                            continue
                        if contact and (target - f[2]) * s < 0:
                            continue
                        lo, hi = b.lo.copy(), b.hi.copy()
                        if s > 0:
                            hi[k] = target
                        else:
                            lo[k] = target
                        if hi[k] - lo[k] < MIN_TH - 1e-9:
                            continue
                        old = (b.lo, b.hi)
                        b.lo, b.hi = lo, hi
                        score = self._count(self.face_list([b], drawn_only=True), buckets, b)
                        b.lo, b.hi = old
                        vol = float(np.prod(b.size()))
                        cand = (score, self._moves.get(id(b), 0), abs(target - f[2]), vol, id(b), b, lo, hi)
                        if best is None or cand[:4] < best[:4]:
                            best = cand
                if best is None:
                    continue
                b = best[5]
                b.lo, b.hi = best[6], best[7]
                self._moves[id(b)] = self._moves.get(id(b), 0) + 1
                touched.add(id(b))
                moved += 1
        raise RuntimeError("resolve: conflits restants apres %d passes" % passes)

    # ------------------------------------------------------------ export
    def _uuid(self):
        self._uid += 1
        return str(_uuid.uuid5(_uuid.NAMESPACE_URL, "medievalships/%s/%d" % (self.name, self._uid)))

    def face_uv(self, b, key):
        mat, mode = b.faces[key]
        U, V, rw, rh = self.atlas.regions[mat]
        k, s = _axis(key)
        # (axe u, signe), (axe v, signe) dans le repere modele (bb : x et z inverses)
        uvax = {"+z": ((0, 1), (1, -1)), "-z": ((0, -1), (1, -1)), "+x": ((2, -1), (1, -1)), "-x": ((2, 1), (1, -1)),
                "+y": ((0, -1), (2, -1)), "-y": ((0, -1), (2, 1))}[key]
        if mode == "stretch":
            return [U, V, U + rw, V + rh]
        out = []
        for (ax, sg), R0, RW in ((uvax[0], U, rw), (uvax[1], V, rh)):
            start = b.lo[ax] if sg > 0 else b.hi[ax]
            w = (b.hi[ax] - b.lo[ax]) * PPB
            off = (sg * start * PPB) % RW
            if w >= RW:
                off, w = 0, RW
            elif off + w > RW:
                off = RW - w
            out.append((R0 + off, R0 + off + w))
        return [round(out[0][0], 4), round(out[1][0], 4), round(out[0][1], 4), round(out[1][1], 4)]

    def export(self, out_models=None, tex_path=None):
        tex_path = tex_path or os.path.join(ASSETS, "textures/entity/%s.png" % self.name)
        png = self.atlas.png(tex_path)
        elements = []

        def bb(p):
            return [round(-p[0] * 16, 4), round(p[1] * 16, 4), round(-p[2] * 16, 4)]

        def group(bone):
            children = []
            for b in bone.boxes:
                frm = [round(-b.hi[0] * 16, 4), round(b.lo[1] * 16, 4), round(-b.hi[2] * 16, 4)]
                to = [round(-b.lo[0] * 16, 4), round(b.hi[1] * 16, 4), round(-b.lo[2] * 16, 4)]
                faces = {}
                for key in KEYS:
                    if b.faces[key] is None or key in b.culled:
                        faces[FACE_BB[key]] = {"uv": [0, 0, 0, 0], "texture": None}
                    else:
                        faces[FACE_BB[key]] = {"uv": self.face_uv(b, key), "texture": 0}
                u = self._uuid()
                c = (b.lo + b.hi) / 2
                elements.append({"name": b.name, "box_uv": False, "rescale": False, "locked": False,
                                 "render_order": "default", "allow_mirror_modeling": True, "from": frm, "to": to,
                                 "autouv": 0, "color": 0, "origin": bb(c), "faces": faces, "type": "cube", "uuid": u})
                children.append(u)
            for ch in bone.children:
                children.append(group(ch))
            return {"name": bone.name, "origin": bb(bone.pivot), "color": 0, "uuid": self._uuid(), "export": True,
                    "mirror_uv": False, "isOpen": False, "locked": False, "visibility": True, "autouv": 0,
                    "children": children}

        outliner = [group(self.root)]
        texture = {"path": "", "name": self.name + ".png", "folder": "entity", "namespace": "medievalships", "id": "0",
                   "group": "", "width": TEX, "height": TEX, "uv_width": TEX, "uv_height": TEX, "particle": False,
                   "use_as_default": True, "layers_enabled": False, "sync_to_project": "", "render_mode": "default",
                   "render_sides": "auto", "frame_time": 1, "frame_order_type": "loop", "frame_order": "",
                   "frame_interpolate": False, "visible": True, "internal": True, "saved": True, "uuid": self._uuid(),
                   "relative_path": "../src/main/resources/assets/medievalships/textures/entity/%s.png" % self.name,
                   "source": "data:image/png;base64," + base64.b64encode(png).decode()}
        model = {"meta": {"format_version": "4.10", "model_format": "free", "box_uv": False}, "name": self.name,
                 "model_identifier": self.name, "visible_box": [14, 11, 0], "variable_placeholders": "",
                 "variable_placeholder_buttons": [], "timeline_setups": [], "unhandled_root_fields": {},
                 "resolution": {"width": TEX, "height": TEX}, "elements": elements, "outliner": outliner,
                 "textures": [texture], "animations": []}
        outs = out_models or [os.path.join(ASSETS, "models/entity/%s.bbmodel" % self.name),
                              os.path.join(ROOT, "blockbench/%s.bbmodel" % self.name)]
        for p in outs:
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w") as f:
                if "resources" in p:
                    json.dump(model, f, separators=(",", ":"))
                else:
                    json.dump(model, f, indent=1)
        return model


# ---------------------------------------------------------------- faces de la structure (agent A), obstacles fixes
def structure_faces(path):
    """Faces dessinees alignees sur les axes du modele de A (os non tournes, cubes non tournes ou tournes de 90 deg)."""
    if not os.path.exists(path):
        return []
    import sys
    sys.path.insert(0, os.path.join(HERE, ".."))
    import preview as pv
    with open(path) as f:
        model = json.load(f)
    out = []
    for corners, uvs, glow, ti in pv.build_mesh(model, {}):
        cs = np.array(corners)
        n = np.cross(cs[1] - cs[0], cs[3] - cs[0])
        L = np.linalg.norm(n)
        if L < 1e-12:
            continue
        n /= L
        k = int(np.argmax(np.abs(n)))
        if abs(n[k]) < 1 - 1e-6:
            continue
        o = [j for j in range(3) if j != k]
        out.append((k, 1 if n[k] > 0 else -1, float(cs[:, k].mean()), cs[:, o[0]].min(), cs[:, o[0]].max(),
                    cs[:, o[1]].min(), cs[:, o[1]].max(), None, "A"))
    return out
