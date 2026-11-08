"""Interior grid of the Fortress Ship: what is solid, dry, a door... in 0.5 block cells.

Same format and cell kinds as tools/frigate_interior.py (read by fr.medievalships.core.InteriorGrid): the grid
gives the collisions of the hull, the decks, the stone bulwarks and parapets, the walls, the stairs and the doors,
the dry rooms and the volume where the players are carried. The model generator (tools/generate_fortress.py)
draws the walls, floors and ceilings of the rooms on the boundaries of these cells, so what is drawn is what
collides.

  src/main/resources/assets/medievalships/interiors/fortress_ship.grid

Layout (docs/Fortress_PLAN.md):
  main deck (4.5): the waist, from the castle's front bulkhead to the forecastle's; the captain's cabin (4.5, no
    step) under the quarterdeck (8.0) at the stern, the crew's mess (4.5) under the forecastle (7.0) at the bow;
    a stair on each side up to the quarterdeck and up to the forecastle, the companionway down to the lower deck
    on the port side between the main and fore masts
  quarterdeck (8.0): the open front of the castle (the helm, the mizzen, the crane), the keep's door, a stair on
    the starboard side up to the keep's roof
  keep (8.0): the officers' room under the keep's roof (11.0); the turret (11.0) on the roof, behind its door
  lower deck (1.0): the cargo hold (aft, under the waist and the cabin) and the crew quarters (forward), a door
    between them; the fore and main masts through it down to the keel
"""
import math
import os
import struct
from collections import deque

import numpy as np

import fortress_shape as fs

OUT, SOLID, DRY, LADDER, AIRLOCK, WINDOW, FURNITURE, DOOR = 0, 1, 2, 3, 4, 5, 6, 16

CELL = fs.CELL
X0, X1 = -7.0, 7.0
Y0, Y1 = -3.5, 15.0
Z0, Z1 = -20.5, 24.0

M = fs.MAIN_DECK_Y          # 4.5
L = fs.LOWER_FLOOR_Y        # 1.0
F = fs.FORECASTLE_Y         # 7.0
Q = fs.QUARTERDECK_Y        # 8.0
K = fs.KEEP_Y               # 11.0
C = fs.CABIN_FLOOR_Y        # 4.5
S = fs.SLAB
CF, KF, FF = fs.CABIN_FRONT_Z, fs.KEEP_FRONT_Z, fs.FC_FRONT_Z
TZ = fs.TRANSOM_Z
TH = fs.TURRET_HALF
TZ0, TZ1 = fs.TURRET_Z

# collision tops of the bulwarks and parapets (1.5 above their deck: nobody steps or jumps over them)
WAIST_WALL = M + 1.5        # stone gunwale 5.5 + the wooden rail between the merlons
FC_WALL = F + 1.5           # stone curb 7.5 + the wooden balustrade
QD_WALL = Q + 1.5           # stone parapet 9.0 + merlons
KEEP_WALL = K + 1.5         # stone parapet 12.0 + merlons

# rooms: (x0, x1, y0, y1, z0, z1), clipped to the inside of the hull (one cell of planking)
ROOMS = {
    "cabin": (-5.5, 5.5, C, Q - S, TZ + 0.5, CF - 0.5),
    "keep": (-5.5, 5.5, Q, K - S, TZ + 0.5, KF - 0.5),
    "turret": (-(TH - 0.5), TH - 0.5, K, K + 3.0, TZ0 + 0.5, TZ1 - 0.5),
    "mess": (-5.0, 5.0, M, F - S, FF + 0.5, 17.0),   # the fore mast through it
    "hold": (-5.5, 5.5, L, M - S, -15.0, fs.CREW_BULKHEAD_Z),
    "crew": (-5.0, 5.0, L, M - S, fs.CREW_BULKHEAD_Z + 0.5, 14.0),
}
# doors: index -> (name, box); 2 wide doors have two leaves
DOORS = {
    0: ("cabin", (-1.0, 1.0, C, Q - S, CF - 0.5, CF)),
    1: ("keep", (-1.0, 1.0, Q, K - S, KF - 0.5, KF)),
    2: ("mess", (-1.0, 1.0, M, F - S, FF, FF + 0.5)),
    3: ("crew", (-1.0, 1.0, L, M - S, fs.CREW_BULKHEAD_Z, fs.CREW_BULKHEAD_Z + 0.5)),
    4: ("turret", (-1.0, 1.0, K, K + 2.5, TZ1 - 0.5, TZ1)),
}
CABIN_DOOR, KEEP_DOOR, MESS_DOOR, CREW_DOOR, TURRET_DOOR = 0, 1, 2, 3, 4
# the masts (1 x 1 block columns, (z, foot)): the fore and main masts stepped on the keel (through the lower
# deck), the mizzen on the quarterdeck
MASTS = [(fs.FORE_MAST_Z, L - S), (fs.MAIN_MAST_Z, L - S), (fs.MIZZEN_Z, Q)]


class Grid:
    def __init__(self):
        self.nx = int(round((X1 - X0) / CELL))
        self.ny = int(round((Y1 - Y0) / CELL))
        self.nz = int(round((Z1 - Z0) / CELL))
        self.k = np.zeros((self.nx, self.ny, self.nz), dtype=np.uint8)
        xs = X0 + (np.arange(self.nx) + 0.5) * CELL
        ys = Y0 + (np.arange(self.ny) + 0.5) * CELL
        zs = Z0 + (np.arange(self.nz) + 0.5) * CELL
        self.X, self.Y, self.Z = np.meshgrid(xs, ys, zs, indexing="ij")
        # outer half width of the hull at each cell (0 outside the length of the hull)
        hx = np.zeros(self.k.shape)
        for j, y in enumerate(ys):
            for l, z in enumerate(zs):
                if TZ < z < fs.FORE_SCALE + 6.0:
                    hx[:, j, l] = fs.hull_x(z, y)
        self.HX = hx

    def sel(self, x0, x1, y0, y1, z0, z1):
        return (self.X > x0) & (self.X < x1) & (self.Y > y0) & (self.Y < y1) & (self.Z > z0) & (self.Z < z1)

    def set(self, kind, x0, x1, y0, y1, z0, z1, where=None):
        m = self.sel(x0, x1, y0, y1, z0, z1)
        if where is not None:
            m &= where
        self.k[m] = kind
        return int(m.sum())

    def inside(self, inset=0.0):
        return np.abs(self.X) < self.HX - inset

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


def stair(g, x0, x1, z_top, z_bottom, y_top, y_bottom):
    """Straight stair of 0.5 x 0.5 steps from y_top (at z_top) down to y_bottom (at z_bottom); the space under the
    steps is solid. Returns the step boxes (x0, x1, top, za, zb)."""
    n = int(round((y_top - y_bottom) / CELL))
    d = math.copysign(CELL, z_bottom - z_top)
    steps = []
    for k in range(1, n):
        top = y_top - k * CELL
        za, zb = sorted((z_top + (k - 1) * d, z_top + k * d))
        g.set(SOLID, x0, x1, y_bottom - CELL, top, za, zb)
        g.set(DRY, x0, x1, top, y_top + 2.5, za, zb, where=g.k != OUT)
        steps.append((x0, x1, top, za, zb))
    return steps


def rising_stair(g, x0, x1, z_foot, direction, y_foot, y_top):
    """Solid steps on an open deck from y_foot up to y_top: the first step's front at z_foot, rising towards
    `direction` (+1 forward, -1 aft)."""
    n = int(round((y_top - y_foot) / CELL))
    for k in range(1, n + 1):
        za = z_foot + direction * (k - 1) * CELL
        g.set(SOLID, x0, x1, y_foot - CELL, y_foot + k * CELL, min(za, za + direction * CELL), max(za, za + direction * CELL))


def build():
    g = Grid()
    hull = g.inside(0.0)
    inner = g.inside(0.5)
    # the hull up to the main deck, to the quarterdeck over the castle, to the keep's roof over the keep, to the
    # forecastle over the mess
    deck_top = np.where(g.Z < KF, K, np.where(g.Z < CF, Q, np.where(g.Z > FF, F, M)))
    g.k[hull & (g.Y < deck_top)] = SOLID
    # the turret on the keep's roof
    g.set(SOLID, -TH, TH, K - 0.01, fs.TURRET_WALL_TOP, TZ0, TZ1)
    # bulwarks and parapets: a shell 0.6 thick on the hull sides, above the decks; the transom closes the stern
    shell = hull & (np.abs(g.X) > g.HX - 0.6)
    wall_top = np.where(g.Z < KF, KEEP_WALL, np.where(g.Z < CF, QD_WALL, np.where(g.Z > FF, FC_WALL, WAIST_WALL)))
    g.k[shell & (g.Y < wall_top)] = SOLID
    g.k[hull & (g.Z < TZ + 0.5) & (g.Y < KEEP_WALL)] = SOLID
    # the keep's parapet along its front
    g.set(SOLID, -7.0, 7.0, K, KEEP_WALL, KF - 0.5, KF, where=hull)
    # the bow: the bulwarks close round the stem
    g.k[hull & (g.Z > fs.DECK_MAX_Z) & (g.Y < FC_WALL)] = SOLID
    # rooms
    for name, box in ROOMS.items():
        g.set(DRY, *box, where=inner if name != "turret" else None)
    # close the rooms where the hull is thinner than a cell (the rising bottom at the ends): no open cell may
    # touch the sea below the main deck
    for _ in range(2):
        room = (g.k == DRY)
        near = np.zeros_like(room)
        near[1:, :, :] |= room[:-1, :, :]
        near[:-1, :, :] |= room[1:, :, :]
        near[:, 1:, :] |= room[:, :-1, :]
        near[:, :-1, :] |= room[:, 1:, :]
        near[:, :, 1:] |= room[:, :, :-1]
        near[:, :, :-1] |= room[:, :, 1:]
        g.k[near & (g.k == OUT) & (g.Y < M - S)] = SOLID
    # stairs: main deck -> quarterdeck (both sides, rising aft), main deck -> forecastle (both sides, rising
    # forward), quarterdeck -> keep's roof (starboard, rising aft), the companionway main deck -> lower deck
    for side in (1, -1):
        xa, xb = sorted((side * fs.QD_STAIR_X[0], side * fs.QD_STAIR_X[1]))
        rising_stair(g, xa, xb, fs.QD_STAIR_Z[0], -1, M, Q)
        xa, xb = sorted((side * fs.FC_STAIR_X[0], side * fs.FC_STAIR_X[1]))
        rising_stair(g, xa, xb, fs.FC_STAIR_Z[0], 1, M, F)
    # inside the keep: the stair from the officers' room up to the roof, through a hatch over its upper steps
    stair(g, fs.KEEP_STAIR_X[0], fs.KEEP_STAIR_X[1], fs.KEEP_STAIR_Z[1], fs.KEEP_STAIR_Z[0], K, Q)
    g.set(DRY, fs.KEEP_STAIR_X[0], fs.KEEP_STAIR_X[1], K - S - 0.01, K + 0.01, fs.KEEP_HATCH_Z[0], fs.KEEP_HATCH_Z[1])
    cx0, cx1 = fs.COMPANION_X
    g.set(DRY, cx0, cx1, M - S - 0.01, M + 0.01, fs.COMPANION_Z[0], fs.COMPANION_Z[1])  # hatch in the main deck
    stair(g, cx0, cx1, fs.COMPANION_Z[1], fs.COMPANION_Z[0], M, L)
    g.set(SOLID, cx1, 6.0, L - S, M - S, fs.COMPANION_Z[0], fs.COMPANION_Z[1], where=inner)  # between the stair and the hull
    # guard rails along the front of the quarterdeck (between the stairs) and of the forecastle (between its stairs)
    g.set(SOLID, -fs.QD_STAIR_X[0], fs.QD_STAIR_X[0], Q, Q + 1.0, CF - 0.5, CF)
    g.set(SOLID, -fs.FC_STAIR_X[0], fs.FC_STAIR_X[0], F, F + 1.0, FF, FF + 0.5)
    # masts through the decks
    for z, foot in MASTS:
        g.set(SOLID, -0.5, 0.5, foot, Y1, z - 0.5, z + 0.5)
    # doors
    for d, (name, box) in DOORS.items():
        g.set(DOOR + d, *box)
    return g


def walkable_report(g):
    """Standing places (1 x 1 block footprint) reachable from the middle of the main deck, every door open:
    returns (reached per room, total)."""
    k = g.k
    passable = (k == OUT) | (k == DRY) | (k == LADDER) | (k >= DOOR)
    solid = (k == SOLID) | (k == FURNITURE) | (k == WINDOW)
    nx, ny, nz = k.shape

    def free(i, j, l):
        if i < 0 or l < 0 or i + 1 >= nx or l + 1 >= nz or j < 1 or j + 4 > ny:
            return False
        return passable[i:i + 2, j:j + 4, l:l + 2].all()

    def stand(i, j, l):
        return free(i, j, l) and solid[i:i + 2, j - 1, l:l + 2].any()

    i0 = int((-0.5 - X0) / CELL)
    j0 = int(round((M - Y0) / CELL))
    l0 = int((-4.0 - Z0) / CELL)
    seen = set()
    q = deque()
    if stand(i0, j0, l0):
        q.append((i0, j0, l0))
        seen.add((i0, j0, l0))
    while q:
        i, j, l = q.popleft()
        for di, dl in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            for dj in (0, 1, -1, -2, -3, -4, -5, -6):
                n = (i + di, j + dj, l + dl)
                if n in seen:
                    continue
                if stand(*n):
                    seen.add(n)
                    q.append(n)
    reached = {}
    for name, (x0, x1, y0, y1, z0, z1) in ROOMS.items():
        reached[name] = sum(1 for (i, j, l) in seen
                            if x0 <= X0 + (i + 1) * CELL <= x1 and abs(Y0 + j * CELL - y0) < 0.6 and z0 <= Z0 + (l + 1) * CELL <= z1)
    reached["quarterdeck"] = sum(1 for (i, j, l) in seen if abs(Y0 + j * CELL - Q) < 0.01 and Z0 + (l + 1) * CELL > KF)
    reached["forecastle"] = sum(1 for (i, j, l) in seen if abs(Y0 + j * CELL - F) < 0.01 and Z0 + (l + 1) * CELL > FF)
    reached["keep_roof"] = sum(1 for (i, j, l) in seen if abs(Y0 + j * CELL - K) < 0.01
                               and not (abs(X0 + (i + 1) * CELL) < TH and TZ0 < Z0 + (l + 1) * CELL < TZ1))
    return reached, len(seen)


GRID_PATH = "src/main/resources/assets/medievalships/interiors/fortress_ship.grid"

if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    g = build()
    size = g.write(os.path.join(root, GRID_PATH))
    counts = {int(k): int((g.k == k).sum()) for k in np.unique(g.k)}
    print("grid", g.nx, g.ny, g.nz, "bytes", size, "cells", counts)
    reached, total = walkable_report(g)
    print("standing places reached from the main deck (doors open):", total)
    for name, n in reached.items():
        print("  %-14s %s" % (name, n if n else "UNREACHABLE"))
