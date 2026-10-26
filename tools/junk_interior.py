"""Interior grid of the Dragon Junk: what is solid, dry, a ladder, a door... in 0.5 block cells.

The grid is the single source of the walkable volume: the mod reads it for the collisions of the hull, the
decks, the bulwarks and balustrades, the walls, the stairs, the stern house and the companion house, for the
ladder and the doors, and for the volume where players are carried along while the junk flies; the model
generator (tools/generate_junk.py) draws the walls, floors and ceilings of the rooms on its boundaries, so
what is drawn is what collides.

  src/main/resources/assets/medievalships/interiors/dragon_junk.grid

Same file format as the Nautilus (tools/nautilus_interior.py): magic b"MSGRID1\\0", int32 nx, ny, nz, float64
x0, y0, z0, float64 cell, then the cells in runs (uint8 kind, varint length), index (ix * nz + iz) * ny + iy.

Layout (docs/JUNK_PLAN.md):
  main deck (0): open from the square bow to the break; a hatch with a ladder down to the storage forward; the
    companion house on the port side of the break (its door faces the bow, a stair inside goes down to the main
    room); the stair up to the quarterdeck on the starboard side; the bedroom door in the break's bulkhead
  quarterdeck (2.5): the helm, the porch, the stern house = the stern cabin (door in its front wall)
  under the quarterdeck (-0.5): the bedroom
  lower deck (-3): the storage forward, the main room amidships (a double door between them)
"""
import math
import struct
from collections import deque

import numpy as np

import junk_shape as js

OUT, SOLID, DRY, LADDER, AIRLOCK, WINDOW, FURNITURE, DOOR = 0, 1, 2, 3, 4, 5, 6, 16

CELL = js.CELL
X0, X1 = -5.0, 5.0
Y0, Y1 = -5.0, 7.5
Z0, Z1 = -20.0, 23.0

M0 = js.MAIN_DECK_Y          # 0
QD = js.QUARTERDECK_Y        # 2.5
LO = js.LOWER_DECK_Y         # -3
BR = js.BEDROOM_Y            # -0.5
HC = js.HOUSE_CEIL_Y         # 6
SLAB = js.SLAB
INF = 30.0

# rooms: (x0, x1, y0, y1, z0, z1), clipped to the inside of the hull
ROOMS = {
    "storage": (-INF, INF, LO, M0 - SLAB, 8.0, 17.0),
    "main_room": (-INF, INF, LO, M0 - SLAB, js.BREAK_Z, 7.5),
    "bedroom": (-INF, INF, BR, QD - SLAB, -9.0, js.BREAK_Z - 0.5),
    "stern_cabin": (-INF, INF, QD, HC, -INF, js.HOUSE_FRONT_Z - 0.5),
    "companion": (1.0, INF, M0, js.MID_WALL_Y, js.MID_Z[0] + 0.5, js.MID_Z[1] - 0.5),
}
# doors: index -> (name, box); 2 block wide doors have two leaves, hatches lie flat
DOORS = {
    0: ("stern_cabin", (-1.0, 1.0, QD, QD + 2.0, js.HOUSE_FRONT_Z - 0.5, js.HOUSE_FRONT_Z)),
    1: ("bedroom", (-0.5, 0.5, M0, M0 + 2.0, js.BREAK_Z - 0.5, js.BREAK_Z)),
    2: ("companion", (1.5, 3.0, M0, M0 + 2.0, js.MID_Z[1] - 0.5, js.MID_Z[1])),
    3: ("storage", (-1.0, 1.0, LO, LO + 2.0, 7.5, 8.0)),
    4: ("hatch", (-0.5, 0.5, M0 - SLAB, M0, 11.0, 12.0)),
}
STERN_DOOR, BEDROOM_DOOR, COMPANION_DOOR, STORAGE_DOOR, HATCH = 0, 1, 2, 3, 4
LADDERS = {
    "hatch": (-0.5, 0.5, LO, M0 - SLAB, 11.0, 12.0),
}
# stairs: (name, x0, x1, z_start, direction (+1: climbs towards the bow), y_start, steps); each step is 0.5 high and
# 0.5 deep, the first step's top at y_start + 0.5 (going up) or y_start - 0.5 (going down)
STAIRS = (
    ("qd", -3.5, -1.5, 0.5, -1, M0, +4),              # main deck -> quarterdeck (starboard), climbing aft
    ("companion", 1.5, 3.0, 3.0, -1, M0, -6),          # companion house -> main room, going down aft
)
COMPANION_HOLE = (1.5, 3.0, 0.0, 3.0)       # opening in the main deck over the companion stair (x0, x1, z0, z1)
HELM_BOX = (-0.5, 0.5, QD, QD + 1.0, js.HELM_Z - 0.25, js.HELM_Z + 0.25)
QD_FRONT_RAIL = (-1.5, 0.5)                # x range of the rail on the quarterdeck's front edge (between the stair and
#                                            the companion house)

FACES = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))


class Grid:
    def __init__(self):
        self.nx = int(round((X1 - X0) / CELL))
        self.ny = int(round((Y1 - Y0) / CELL))
        self.nz = int(round((Z1 - Z0) / CELL))
        self.k = np.zeros((self.nx, self.ny, self.nz), dtype=np.uint8)
        xs = X0 + (np.arange(self.nx) + 0.5) * CELL
        ys = Y0 + (np.arange(self.ny) + 0.5) * CELL
        zs = Z0 + (np.arange(self.nz) + 0.5) * CELL
        self.xs, self.ys, self.zs = xs, ys, zs
        self.X, self.Y, self.Z = np.meshgrid(xs, ys, zs, indexing="ij")

    def sel(self, x0, x1, y0, y1, z0, z1):
        """Cells whose centre lies in the box."""
        return (self.X > x0) & (self.X < x1) & (self.Y > y0) & (self.Y < y1) & (self.Z > z0) & (self.Z < z1)

    def set(self, kind, x0, x1, y0, y1, z0, z1, where=None):
        m = self.sel(x0, x1, y0, y1, z0, z1)
        if where is not None:
            m &= where
        self.k[m] = kind
        return int(m.sum())

    def at(self, x, y, z):
        i = int(math.floor((x - X0) / CELL))
        j = int(math.floor((y - Y0) / CELL))
        k = int(math.floor((z - Z0) / CELL))
        return int(self.k[i, j, k])

    def write(self, path):
        flat = self.k.transpose(0, 2, 1).reshape(-1)  # (ix, iz, iy): columns along y
        out = bytearray(b"MSGRID1\0")
        out += struct.pack("<3i4d", self.nx, self.ny, self.nz, X0, Y0, Z0, CELL)
        i, n = 0, len(flat)
        while i < n:
            kind = flat[i]
            j = i
            while j < n and flat[j] == kind:
                j += 1
            out.append(int(kind))
            run = j - i
            while True:
                b = run & 0x7F
                run >>= 7
                out.append(b | (0x80 if run else 0))
                if not run:
                    break
            i = j
        with open(path, "wb") as f:
            f.write(out)
        return len(out)


def _vec(fn, *arrays):
    return np.vectorize(fn, otypes=[float])(*arrays)


def stair_steps(st):
    """(x0, x1, z0, z1, top) of each step of a stair."""
    name, x0, x1, zs, d, y0, n = st
    out = []
    up = n > 0
    for k in range(abs(n)):
        za = zs + d * 0.5 * k
        zb = za + d * 0.5
        top = y0 + 0.5 * (k + 1) if up else y0 - 0.5 * (k + 1)
        out.append((x0, x1, min(za, zb), max(za, zb), top))
    return out


def mast_cells(g, y0, y1, r=0.45):
    """Cells of the raked mast between two heights."""
    zc = np.array([js.mast_point(y)[2] for y in g.ys])
    m = (np.abs(g.X) < r) & (np.abs(g.Z - zc[None, :, None]) < r) & (g.Y > y0) & (g.Y < y1)
    return m


def build():
    g = Grid()
    X, Y, Z = g.X, g.Y, g.Z
    hx = _vec(js.hull_x, Z, Y)
    keel = _vec(js.keel_y, Z)
    sheer = _vec(js.sheer_y, Z)
    deck = _vec(js.deck_y, Z)
    # ---- hull: solid planking and decks; open air above the open decks
    body = (np.abs(X) <= hx) & (Y >= keel) & (Y <= sheer) & (hx > 0.2)
    g.k[body] = SOLID
    inner = body & (np.abs(X) <= hx - js.SHELL) & (Y >= keel + js.SHELL) & (Z < js.BOW_Z - js.SHELL) & (Z > js.STERN_Z + js.SHELL)
    g.k[inner & (Y > deck)] = OUT
    # ---- the stern house on the quarterdeck: walls on the hull's sides, its front wall, the transom, the ceiling
    hx_top = _vec(js.hull_x, Z, np.full(Z.shape, QD - 0.1))
    house = (Z <= js.HOUSE_FRONT_Z) & (Z >= js.STERN_Z) & (np.abs(X) <= hx_top) & (Y >= QD - SLAB) & (Y <= HC + SLAB) & (hx_top > 0.2)
    g.k[house] = SOLID
    # ---- the companion house on the port side of the break: walls, roof slab, its floor is the main deck
    hx_mid = _vec(js.hull_x, Z, np.full(Z.shape, 0.5))
    mid = (X >= js.MID_X[0]) & (X <= hx_mid) & (Z >= js.MID_Z[0]) & (Z <= js.MID_Z[1]) & (Y >= M0 - SLAB) & (Y <= js.MID_WALL_Y + SLAB)
    g.k[mid] = SOLID
    # ---- rooms: a solid cell between them and the outside across every face (also at the bow, the transom and
    # under the curve of the bilge), so no room opens on the air
    shell = body | house | mid
    enclosed = shell.copy()
    for o in FACES:
        enclosed &= np.roll(shell, o, axis=(0, 1, 2))
    for name, box in ROOMS.items():
        g.set(DRY, *box, where=enclosed)
    # ---- the balustrade of the quarterdeck along the sides (the outermost cells), across its front edge
    rail_layer = (Y > QD) & (Y < QD + js.RAIL_H)
    edge = (np.abs(X) <= hx_top) & (np.abs(X) > hx_top - CELL) & (Z < js.BREAK_Z) & (Z > js.HOUSE_FRONT_Z) & (hx_top > 0.2)
    g.k[edge & rail_layer & (g.k == OUT)] = FURNITURE
    g.set(FURNITURE, QD_FRONT_RAIL[0], QD_FRONT_RAIL[1], QD, QD + js.RAIL_H, js.BREAK_Z - 0.5, js.BREAK_Z, where=g.k == OUT)
    # ---- stairs (steps are furniture: drawn by the model, not by the room surfaces)
    hole = COMPANION_HOLE
    g.set(DRY, hole[0], hole[1], M0 - SLAB, M0, hole[2], hole[3])
    for st in STAIRS:
        for x0, x1, z0, z1, top in stair_steps(st):
            if st[6] > 0:
                g.set(FURNITURE, x0, x1, st[5], top, z0, z1)   # outside: solid down to the deck
            else:
                g.set(FURNITURE, x0, x1, top - 0.5, top, z0, z1)
    # ---- the mast's foot on the main deck (above head height it is out of reach), the helm
    g.k[mast_cells(g, M0, M0 + 3.5) & (g.k == OUT)] = FURNITURE
    g.k[mast_cells(g, LO - SLAB, M0 - SLAB) & (g.k == DRY)] = FURNITURE   # its heel, stepped on the keel in the storage
    g.set(FURNITURE, *HELM_BOX)
    # ---- ladder, doors (after everything: they cut through walls, decks and rails)
    for name, box in LADDERS.items():
        g.set(LADDER, *box)
    for d, (name, box) in DOORS.items():
        g.set(DOOR + d, *box)
    return g


def walkable_report(g, start=(0.0, M0 + 0.01, 9.0)):
    """Standing places (1 x 1 block footprint) reachable from the main deck with every door open: returns
    (reached per room, total)."""
    k = g.k
    passable = (k == OUT) | (k == DRY) | (k == LADDER) | (k >= DOOR)
    solid = ~passable
    lad = k == LADDER
    nx, ny, nz = k.shape

    def free(i, j, l):
        if i < 0 or l < 0 or i + 1 >= nx or l + 1 >= nz or j < 0 or j + 4 > ny:
            return False
        return passable[i:i + 2, j:j + 4, l:l + 2].all()

    def stand(i, j, l):
        if not free(i, j, l):
            return False
        if lad[i:i + 2, max(0, j - 1):j + 1, l:l + 2].any():   # the game climbs with the feet 0.45 above a rung
            return True
        return j > 0 and solid[i:i + 2, j - 1, l:l + 2].any()

    i0 = int((start[0] - 0.5 - X0) / CELL)
    j0 = int((start[1] - Y0) / CELL)
    l0 = int((start[2] - Z0) / CELL)
    seen = set()
    q = deque()
    if stand(i0, j0, l0):
        q.append((i0, j0, l0))
        seen.add((i0, j0, l0))
    while q:
        i, j, l = q.popleft()
        onlad = lad[i:i + 2, j:j + 2, l:l + 2].any()
        for di, dl in ((1, 0), (-1, 0), (0, 1), (0, -1), (0, 0)):
            for dj in ((-1, 0, 1) if (di or dl) else ()) + ((1, -1) if onlad else ()) + ((-1, -2, -3, -4, -5, -6) if (di or dl) else ()):
                n = (i + di, j + dj, l + dl)
                if n in seen:
                    continue
                if stand(*n):
                    seen.add(n)
                    q.append(n)
    reached = {}
    places = dict(ROOMS)
    places["main_deck"] = (-INF, INF, M0, M0 + 0.4, js.BREAK_Z, INF)
    places["quarterdeck"] = (-INF, INF, QD, QD + 0.4, js.HOUSE_FRONT_Z, js.BREAK_Z)
    for name, (x0, x1, y0, y1, z0, z1) in places.items():
        cells = [(i, j, l) for (i, j, l) in seen
                 if x0 <= X0 + (i + 1) * CELL <= x1 and y0 - 0.1 <= Y0 + j * CELL <= y1 and z0 <= Z0 + (l + 1) * CELL <= z1]
        reached[name] = len(cells)
    return reached, len(seen)


def leaks(g):
    """Cells of the rooms (dry or ladder) that touch the outside air across a face: none."""
    k = g.k
    room = (k == DRY) | (k == LADDER)
    out = k == OUT
    touch = np.zeros_like(room)
    for o in FACES:
        touch |= np.roll(out, o, axis=(0, 1, 2))
    bad = room & touch
    return [(float(g.xs[i]), float(g.ys[j]), float(g.zs[l])) for i, j, l in zip(*np.nonzero(bad))]


GRID_PATH = "src/main/resources/assets/medievalships/interiors/dragon_junk.grid"

if __name__ == "__main__":
    g = build()
    counts = {int(k): int((g.k == k).sum()) for k in np.unique(g.k)}
    print("grid", g.nx, g.ny, g.nz, "cells", counts)
    lk = leaks(g)
    print("room cells open on the outside:", len(lk), lk[:10])
    reached, total = walkable_report(g)
    print("standing places reached from the main deck (doors open):", total)
    for name, n in reached.items():
        print("  %-16s %s" % (name, n if n else "UNREACHABLE"))
