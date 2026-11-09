"""Interior grid of the Royal Lion Ship: what is solid, dry, a door... in 0.5 block cells.

Same format and cell kinds as tools/frigate_interior.py (read by fr.medievalships.core.InteriorGrid): the grid
gives the collisions of the hull, the decks, the bulwarks, the walls, the stairs and the doors, the dry rooms and
the volume where the players are carried. The model generator (tools/generate_royal_lion.py) draws the walls,
floors and ceilings of the rooms on the boundaries of these cells, so what is drawn is what collides.

  src/main/resources/assets/medievalships/interiors/royal_lion_ship.grid

Layout (docs/RoyalLion_PLAN.md):
  quarterdeck (8.5): the helm under the striped awning, the mizzen; the roundhouse over its aft part (the upper
    storey of the castle, 8 blocks long): the royal state room (8.5 -> 12.0, under the blue mansard roof), a double
    door on each side of the mizzen in its front wall
  main deck (5.0): open from the cabin bulkhead to the forecastle; the captain's cabin (5.0, no step) under the
    quarterdeck, a stair on each side up to the quarterdeck, a stair on each side up to the forecastle (7.0);
    two companionways down: starboard of the centre to the crew quarters, on the port side to the cargo hold
  lower deck (1.5): the crew quarters aft and the cargo hold forward, a bulkhead with a double door between them;
    the fore and main masts through the hold down to the keel
"""
import math
import os
import struct
from collections import deque

import numpy as np

import royal_lion_shape as fs

OUT, SOLID, DRY, LADDER, AIRLOCK, WINDOW, FURNITURE, DOOR = 0, 1, 2, 3, 4, 5, 6, 16

CELL = fs.CELL
X0, X1 = -7.0, 7.0
Y0, Y1 = -4.5, 14.0
Z0, Z1 = -22.5, 26.0

M = fs.MAIN_DECK_Y          # 4.5
L = fs.LOWER_FLOOR_Y        # 1.0
Q = fs.QUARTERDECK_Y        # 8.0
C = fs.CABIN_FLOOR_Y        # 4.5
F = fs.FORECASTLE_Y         # 6.0
S = fs.SLAB
RH0, RH1 = fs.ROUNDHOUSE_FLOOR_Y, fs.ROUNDHOUSE_CEIL_Y
RF = fs.ROUNDHOUSE_FRONT_Z  # -16.0
B0, B1 = fs.BULKHEAD_Z

# rooms: (x0, x1, y0, y1, z0, z1), clipped to the inside of the hull (one cell of planking)
ROOMS = {
    "cabin": (-5.0, 5.0, C, Q - S, fs.TRANSOM_Z + 0.5, fs.CABIN_FRONT_Z - 0.5),
    "stateroom": (-5.0, 5.0, RH0, RH1, fs.TRANSOM_Z + 0.5, RF - 0.5),
    "crew": (-5.5, 5.5, L, M - S, fs.LOWER_AFT_Z, B0),
    "hold": (-5.5, 5.5, L, M - S, B1, fs.LOWER_FORE_Z),
}
# doors: index -> (name, box); 2 wide doors have two leaves
DOORS = {
    0: ("cabin", (-1.0, 1.0, C, Q - S, fs.CABIN_FRONT_Z - 0.5, fs.CABIN_FRONT_Z)),
    1: ("stateroom", (1.0, 2.5, RH0, RH0 + 2.5, RF - 0.5, RF)),          # port of the mizzen
    2: ("bulkhead", (-1.0, 1.0, L, L + 2.5, B0, B1)),
    3: ("stateroom_s", (-2.5, -1.0, RH0, RH0 + 2.5, RF - 0.5, RF)),      # starboard of the mizzen
}
CABIN_DOOR, STATEROOM_DOOR, BULKHEAD_DOOR, STATEROOM_DOOR_S = 0, 1, 2, 3
# the masts (1 x 1 block columns, (z, foot)): the fore and main masts stepped on the keel (through the hold), the
# mizzen on the quarterdeck
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
                if fs.TRANSOM_Z < z < fs.FORE_SCALE + 4.0:
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
    """Straight stair of 0.5 x 0.5 steps from y_top (at z_top) down to y_bottom (at z_bottom); the space under
    the steps is solid. Returns the step boxes (x0, x1, top, za, zb)."""
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


def companion(g, xr, zr, deck, floor):
    """A companionway: the hatch in the deck and the stair down (from zr[1] at the deck to zr[0] at the floor),
    solid on both sides of it under the deck (the hull side or a partition)."""
    x0, x1 = xr
    g.set(DRY, x0, x1, deck - S - 0.01, deck + 0.01, zr[0], zr[1])
    stair(g, x0, x1, zr[1], zr[0], deck, floor)


def build():
    g = Grid()
    hull = g.inside(0.0)
    inner = g.inside(0.5)
    # the hull up to the walking deck (the quarterdeck over the captain's cabin, the raised forecastle) is solid
    deck_top = np.where(g.Z < fs.CABIN_FRONT_Z, Q, np.where(g.Z > fs.FORECASTLE_Z, F, M))
    g.k[hull & (g.Y < deck_top)] = SOLID
    # bulwarks: a shell 0.6 thick on the hull sides, above the decks; the transom closes the stern
    shell = hull & (np.abs(g.X) > g.HX - 0.6)
    bul_top = np.where(g.Z < fs.CABIN_FRONT_Z, fs.QD_BULWARK_TOP, np.where(g.Z > fs.FORECASTLE_Z, fs.FC_BULWARK_TOP, fs.BULWARK_TOP))
    g.k[shell & (g.Y < bul_top)] = SOLID
    g.k[hull & (g.Z < fs.TRANSOM_Z + 0.5) & (g.Y < fs.QD_BULWARK_TOP)] = SOLID
    # the bow: the bulwarks close round the stem
    g.k[hull & (g.Z > fs.DECK_MAX_Z) & (g.Y < fs.FC_BULWARK_TOP + 0.5)] = SOLID
    # the roundhouse on the quarterdeck: its walls (the hull shell, the stern, the front wall) up to its roof slab
    rh = hull & (g.Z < RF) & (g.Y >= Q) & (g.Y < RH1 + S)
    g.k[rh & ((np.abs(g.X) > g.HX - 0.6) | (g.Z < fs.TRANSOM_Z + 0.5) | (g.Z > RF - 0.5) | (g.Y > RH1))] = SOLID
    # rooms
    for name, box in ROOMS.items():
        g.set(DRY, *box, where=inner)
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
    # the bulkhead between the crew quarters and the hold
    g.set(SOLID, -6.0, 6.0, L - 0.01, M - S + 0.01, B0, B1, where=hull)
    # stairs: main deck -> quarterdeck (both sides, rising aft), main deck -> forecastle (both sides, rising
    # forward), the two companionways down to the lower deck
    for side in (1, -1):
        xa, xb = sorted((side * fs.QD_STAIR_X[0], side * fs.QD_STAIR_X[1]))
        n = int(round((Q - M) / CELL))
        for k in range(1, n + 1):
            za = fs.QD_STAIR_Z[0] - k * CELL
            g.set(SOLID, xa, xb, M - CELL, M + k * CELL, za, za + CELL)
        xa, xb = sorted((side * fs.FC_STAIR_X[0], side * fs.FC_STAIR_X[1]))
        n = int(round((F - M) / CELL))
        for k in range(1, n + 1):
            za = fs.FC_STAIR_Z[0] + (k - 1) * CELL
            g.set(SOLID, xa, xb, M - CELL, M + k * CELL, za, za + CELL)
    companion(g, fs.CREW_STAIR_X, fs.CREW_STAIR_Z, M, L)
    companion(g, fs.HOLD_STAIR_X, fs.HOLD_STAIR_Z, M, L)
    g.set(SOLID, fs.HOLD_STAIR_X[1], 5.5, L - S, M - S, fs.HOLD_STAIR_Z[0], fs.HOLD_STAIR_Z[1], where=inner)  # stair -> hull
    # guard rails along the front of the quarterdeck (between its stairs) and the back of the forecastle
    g.set(SOLID, -fs.QD_STAIR_X[0], fs.QD_STAIR_X[0], Q, Q + 1.0, fs.CABIN_FRONT_Z - 0.5, fs.CABIN_FRONT_Z)
    g.set(SOLID, -fs.FC_STAIR_X[0], fs.FC_STAIR_X[0], F, F + 1.0, fs.FORECASTLE_Z, fs.FORECASTLE_Z + 0.5)
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
    l0 = int((1.5 - Z0) / CELL)
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
    reached["quarterdeck"] = sum(1 for (i, j, l) in seen if abs(Y0 + j * CELL - Q) < 0.01 and Z0 + (l + 1) * CELL > RF)
    reached["forecastle"] = sum(1 for (i, j, l) in seen if abs(Y0 + j * CELL - F) < 0.01)
    return reached, len(seen)


GRID_PATH = "src/main/resources/assets/medievalships/interiors/royal_lion_ship.grid"

if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    g = build()
    counts = {int(k): int((g.k == k).sum()) for k in np.unique(g.k)}
    print("grid", g.nx, g.ny, g.nz, "cells", counts)
    reached, total = walkable_report(g)
    print("standing places reached from the main deck (doors open):", total)
    for name, n in reached.items():
        print("  %-14s %s" % (name, n if n else "UNREACHABLE"))
