"""Interior grid of the Nautilus: what is solid, dry, a ladder, a door... in 0.5 block cells.

The grid is the single source of the interior: the mod reads it for the collisions of the walls,
floors and stairs, the dry compartments (no water inside, even deep under the sea), the ladders
and the doors; the model generator draws the walls, floors and ceilings on its boundaries, so what
is drawn is what collides.

  src/main/resources/assets/medievalships/interiors/nautilus.grid

File format (little endian): magic b"MSGRID1\\0", int32 nx, ny, nz, float64 x0, y0, z0 (local
corner of cell 0, 0, 0), float64 cell, then the cells in runs (uint8 kind, varint length), index
(ix * nz + iz) * ny + iy (columns along y).
"""
import math
import struct

import numpy as np

import nautilus_shape as ns

# cell kinds (same values in InteriorGrid.java)
OUT = 0        # outside the hull: the sea (or the air above it)
SOLID = 1      # hull, walls, floors, ceilings, tanks, machinery
DRY = 2        # air inside a watertight compartment
LADDER = 3     # dry, and climbable
AIRLOCK = 4    # dry or flooded, depending on the airlock
DOOR = 16      # DOOR + k: door k (solid when closed, dry when open), k < 32

CELL = ns.CELL
X0, X1 = -8.0, 8.0
Y0, Y1 = -9.0, 16.0
Z0, Z1 = -49.0, 49.0


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

    def sel(self, x0, x1, y0, y1, z0, z1):
        """Cells whose centre lies in the box."""
        return ((self.X > x0) & (self.X < x1) & (self.Y > y0) & (self.Y < y1) & (self.Z > z0) & (self.Z < z1))

    def set(self, kind, x0, x1, y0, y1, z0, z1, where=None):
        m = self.sel(x0, x1, y0, y1, z0, z1)
        if where is not None:
            m &= where
        self.k[m] = kind
        return int(m.sum())

    def inside(self, inset):
        w = np.vectorize(ns.half_width)(self.Z) - inset
        h = np.vectorize(ns.half_height)(self.Z) - inset
        ok = (w > 0) & (h > 0)
        w = np.where(ok, w, 1.0)
        h = np.where(ok, h, 1.0)
        return ok & ((self.X / w) ** 2 + ((self.Y - ns.AXIS_Y) / h) ** 2 <= 1.0)

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


# ---- layout of the spaces (prototype: will grow room by room, see docs/NAUTILUS_PLAN.md)
MAIN_HALL = (-3.0, 3.0, ns.MAIN_FLOOR_Y, ns.MAIN_FLOOR_Y + ns.LEVEL_HEIGHT, -26.0, 28.0)
LOWER_HALL = (-2.5, 2.5, ns.LOWER_FLOOR_Y, ns.LOWER_FLOOR_Y + 4.0, -20.0, 20.0)
STAIR_X = (-2.5, -1.0)
STAIR_Z0 = 10.0          # first step of the stairs from the lower level up to the main level
HATCH_Z = (18.0, 19.0)   # ladder shaft and hatch to the top of the hull
HATCH_X = (-0.5, 0.5)
HATCH_DOOR = 0
TOWER_Z = (25.0, 31.0)   # wheelhouse on top of the hull
TOWER_X = (-2.0, 2.0)
TOWER_FLOOR_Y = 6.5
TOWER_HEIGHT = 3.0
TOWER_SHAFT_Z = (25.5, 26.5)
PILOT_Z = 29.6


def build():
    g = Grid()
    hull = g.inside(0.0)
    g.k[hull] = SOLID
    inner = g.inside(ns.SHELL)
    # main level, lower level
    g.set(DRY, *MAIN_HALL, where=inner)
    g.set(DRY, *LOWER_HALL, where=inner)
    # stairs from the lower level to the main level: 9 steps of 0.5, opening in the main floor
    rise = ns.MAIN_FLOOR_Y - ns.LOWER_FLOOR_Y
    steps = int(round(rise / CELL))
    x0, x1 = STAIR_X
    g.set(DRY, x0, x1, ns.LOWER_FLOOR_Y, ns.MAIN_FLOOR_Y + 0.01, STAIR_Z0, STAIR_Z0 + steps * CELL)
    for i in range(steps):
        z = STAIR_Z0 + i * CELL
        g.set(SOLID, x0, x1, ns.LOWER_FLOOR_Y - 0.01, ns.LOWER_FLOOR_Y + (i + 1) * CELL, z, z + CELL)
    # ladder up to the hatch on the top of the hull
    top = ns.hull_top((HATCH_Z[0] + HATCH_Z[1]) / 2, 0.5)
    g.set(LADDER, HATCH_X[0], HATCH_X[1], ns.MAIN_FLOOR_Y, top - ns.SHELL, *HATCH_Z)
    g.set(DOOR + HATCH_DOOR, HATCH_X[0], HATCH_X[1], top - ns.SHELL, top + 0.3, *HATCH_Z, where=g.k != OUT)
    # wheelhouse: armoured box on the top of the hull, floor at TOWER_FLOOR_Y, ladder from the main level
    tx0, tx1 = TOWER_X
    tz0, tz1 = TOWER_Z
    ty0, ty1 = TOWER_FLOOR_Y - ns.SHELL, TOWER_FLOOR_Y + TOWER_HEIGHT + ns.SHELL
    g.set(SOLID, tx0, tx1, 0.0, ty1, tz0, tz1, where=(g.k == OUT) & (g.Y > 2.0))
    g.set(DRY, tx0 + ns.SHELL, tx1 - ns.SHELL, TOWER_FLOOR_Y, TOWER_FLOOR_Y + TOWER_HEIGHT, tz0 + ns.SHELL, tz1 - ns.SHELL)
    g.set(LADDER, HATCH_X[0], HATCH_X[1], ns.MAIN_FLOOR_Y, TOWER_FLOOR_Y + 1.0, *TOWER_SHAFT_Z)
    # in the hall, each ladder is fixed against a pillar (something to hold on and to push against)
    for z_top in (HATCH_Z[1], TOWER_SHAFT_Z[1]):
        g.set(SOLID, HATCH_X[0], HATCH_X[1], ns.MAIN_FLOOR_Y, ns.MAIN_FLOOR_Y + ns.LEVEL_HEIGHT, z_top, z_top + CELL)
    return g


GRID_PATH = "src/main/resources/assets/medievalships/interiors/nautilus.grid"

if __name__ == "__main__":
    import os
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    g = build()
    path = os.path.join(root, GRID_PATH)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    size = g.write(path)
    counts = {k: int((g.k == k).sum()) for k in np.unique(g.k)}
    print("grid", g.nx, g.ny, g.nz, "bytes", size, "cells", counts)
