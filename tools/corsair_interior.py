"""Interior grid of the Old Corsair: what is solid, dry, a ladder, a door... in 0.5 block cells.

Same format and cell kinds as tools/nautilus_interior.py (read by fr.medievalships.core.InteriorGrid):
the grid gives the collisions of the hull, the decks, the bulwarks, the walls, the stairs and the
doors, the dry rooms below the waterline (the hold) and the volume where the players are carried.
The model generator (tools/generate_corsair.py) draws the walls, floors and ceilings of the rooms on
the boundaries of these cells, so what is drawn is what collides.

  src/main/resources/assets/medievalships/interiors/old_corsair.grid

Layout (docs/CORSAIR_PLAN.md):
  main deck (4.5): open from the cabin bulkhead to the bow; the captain's cabin (4.0) under the
    quarterdeck (7.0) at the stern, a stair on each side up to the quarterdeck, the companionway down to the
    common room on the port side, between the two masts
  lower deck (1.0): coursive along the centre line with the crew quarters on each side (the main mast,
    stepped on the main deck, stays above it), the common room (fore mast through it), the kitchen forward
  hold (-2.0): under the whole lower deck, reached by the stair at the aft end of the coursive
"""
import math
import os
import struct
from collections import deque

import numpy as np

import corsair_shape as cs

OUT, SOLID, DRY, LADDER, AIRLOCK, WINDOW, FURNITURE, DOOR = 0, 1, 2, 3, 4, 5, 6, 16

CELL = cs.CELL
X0, X1 = -6.0, 6.0
Y0, Y1 = -4.5, 10.5
Z0, Z1 = -23.0, 25.0

M = cs.MAIN_DECK_Y          # 4.5
L = cs.LOWER_FLOOR_Y        # 1.0
H = cs.HOLD_FLOOR_Y         # -2.0
Q = cs.QUARTERDECK_Y        # 7.0
C = cs.CABIN_FLOOR_Y        # 4.0
S = cs.SLAB

# rooms: (x0, x1, y0, y1, z0, z1), clipped to the inside of the hull (one cell of planking)
ROOMS = {
    "cabin":        (-4.5, 4.5, C, Q - S, cs.TRANSOM_Z + 0.5, cs.CABIN_FRONT_Z - 0.5),
    "coursive":     (-1.0, 1.0, L, M - S, cs.HOLD_STAIR_Z[1], -1.5),
    "hold_stairs":  (-1.0, 1.0, H, C - S, cs.HOLD_STAIR_Z[0], cs.HOLD_STAIR_Z[1]),
    "crew_port":    (1.5, 4.5, L, M - S, -13.0, -1.5),
    "crew_stbd":    (-4.5, -1.5, L, M - S, -13.0, -1.5),
    "common_room":  (-4.5, 4.5, L, M - S, -1.0, 8.0),
    "kitchen":      (-4.5, 4.5, L, M - S, 8.5, 14.0),
    "hold":         (-4.5, 4.5, H, L - S, cs.HOLD_STAIR_Z[0], 13.0),
}
# doors: index -> (name, box); 2 wide doors have two leaves
DOORS = {
    0: ("cabin", (-1.0, 1.0, C, Q - S, cs.CABIN_FRONT_Z - 0.5, cs.CABIN_FRONT_Z)),
    1: ("coursive_common", (-1.0, 1.0, L, L + 2.0, -1.5, -1.0)),
    2: ("common_kitchen", (-1.0, 1.0, L, L + 2.0, 8.0, 8.5)),
    3: ("crew_port", (1.0, 1.5, L, L + 2.0, -7.5, -6.5)),
    4: ("crew_stbd", (-1.5, -1.0, L, L + 2.0, -7.5, -6.5)),
}
CABIN_DOOR = 0
# the two masts (1 x 1 block columns, (z, foot)): the fore mast stepped on the keel (through the common
# room and the hold), the main mast on the main deck
MASTS = [(cs.FORE_MAST_Z, H - S), (cs.MAIN_MAST_Z, M)]


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
                if cs.TRANSOM_Z < z < cs.FORE_SCALE + 3.0:
                    hx[:, j, l] = cs.hull_x(z, y)
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
    """Straight stair of 0.5 x 0.5 steps from y_top (at z_top) down to y_bottom (at z_bottom); the
    space under the steps is solid. Returns the step boxes (x0, x1, top, za, zb)."""
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


def build():
    g = Grid()
    hull = g.inside(0.0)
    inner = g.inside(0.5)
    # the hull up to the main deck (or to the quarterdeck over the captain's cabin) is solid
    deck_top = np.where(g.Z < cs.CABIN_FRONT_Z, Q, M)
    g.k[hull & (g.Y < deck_top)] = SOLID
    # bulwarks: a shell 0.6 thick on the hull sides, above the decks; the transom closes the stern
    shell = hull & (np.abs(g.X) > g.HX - 0.6)
    bul_top = np.where(g.Z < cs.CABIN_FRONT_Z, cs.QD_BULWARK_TOP, cs.BULWARK_TOP)
    g.k[shell & (g.Y < bul_top)] = SOLID
    g.k[hull & (g.Z < cs.TRANSOM_Z + 0.5) & (g.Y < cs.QD_BULWARK_TOP)] = SOLID
    # the bow: the bulwarks close round the stem
    g.k[hull & (g.Z > cs.DECK_MAX_Z) & (g.Y < cs.BULWARK_TOP + 0.5)] = SOLID
    # rooms
    for name, box in ROOMS.items():
        g.set(DRY, *box, where=inner)
    # close the rooms where the hull is thinner than a cell (the rising bottom at the ends): no open
    # cell may touch the sea below the main deck
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
    # stairs: main deck -> quarterdeck (both sides, rising aft), the companionway main deck -> common room,
    # the hold stair at the aft end of the coursive
    for side in (1, -1):
        xa, xb = sorted((side * cs.QD_STAIR_X[0], side * cs.QD_STAIR_X[1]))
        n = int(round((Q - M) / CELL))
        for k in range(1, n + 1):
            za = cs.QD_STAIR_Z[0] - k * CELL
            g.set(SOLID, xa, xb, M - CELL, M + k * CELL, za, za + CELL)
    cx0, cx1 = cs.COMPANION_X
    g.set(DRY, cx0, cx1, M - S - 0.01, M + 0.01, cs.COMPANION_Z[0], cs.COMPANION_Z[1])  # hatch in the main deck
    stair(g, cx0, cx1, cs.COMPANION_Z[1], cs.COMPANION_Z[0], M, L)
    g.set(SOLID, cx1, 4.5, L - S, M - S, cs.COMPANION_Z[0], cs.COMPANION_Z[1], where=inner)  # between the stair and the hull
    hx0, hx1 = cs.HOLD_STAIR_X
    g.set(DRY, hx0, hx1, L - S - 0.01, L + 0.01, cs.HOLD_STAIR_Z[0], cs.HOLD_STAIR_Z[1])
    stair(g, hx0, hx1, cs.HOLD_STAIR_Z[1], cs.HOLD_STAIR_Z[0], L, H)
    # a guard rail along the front of the quarterdeck, between the stairs
    g.set(SOLID, -cs.QD_STAIR_X[0], cs.QD_STAIR_X[0], Q, Q + 1.0, cs.CABIN_FRONT_Z - 0.5, cs.CABIN_FRONT_Z)
    # masts through the decks
    for z, foot in MASTS:
        g.set(SOLID, -0.5, 0.5, foot, Y1, z - 0.5, z + 0.5)
    # doors
    for d, (name, box) in DOORS.items():
        g.set(DOOR + d, *box)
    return g


def walkable_report(g):
    """Standing places (1 x 1 block footprint) reachable from the middle of the main deck, every door
    open: returns (reached per room, total)."""
    k = g.k
    passable = (k == OUT) | (k == DRY) | (k == LADDER) | (k >= DOOR)
    solid = (k == SOLID) | (k == FURNITURE) | (k == WINDOW)
    nx, ny, nz = k.shape
    inside_xy = np.zeros(k.shape, dtype=bool)
    inside_xy[...] = g.HX > 0.3

    def free(i, j, l):
        if i < 0 or l < 0 or i + 1 >= nx or l + 1 >= nz or j < 1 or j + 4 > ny:
            return False
        return passable[i:i + 2, j:j + 4, l:l + 2].all()

    def stand(i, j, l):
        # on a floor (solid under one of the cells) of the ship (not the sea: outside the hull nothing is solid)
        return free(i, j, l) and solid[i:i + 2, j - 1, l:l + 2].any()

    i0 = int((-0.5 - X0) / CELL)
    j0 = int(round((M - Y0) / CELL))
    l0 = int((-3.0 - Z0) / CELL)
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
    reached["quarterdeck"] = sum(1 for (i, j, l) in seen if abs(Y0 + j * CELL - Q) < 0.01)
    return reached, len(seen)


GRID_PATH = "src/main/resources/assets/medievalships/interiors/old_corsair.grid"

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
