"""Interior grid of the Rustic Skyskiff: what is solid, dry, a ladder, a window, a door... in 0.5 block cells.

The grid is the single source of the walkable volume: the mod reads it for the collisions of the hull, the
decks, the walls, the stairs and the balustrades, for the ladder and the doors, and for the volume where
players are carried along; the model generator draws the walls, floors and ceilings of the rooms on its
boundaries, so what is drawn is what collides.

  src/main/resources/assets/medievalships/interiors/rustic_skiff.grid

Same file format as the Nautilus and the Sky Leviathan (tools/leviathan_interior.py): magic b"MSGRID1\\0",
int32 nx, ny, nz, float64 x0, y0, z0, float64 cell, then the cells in runs (uint8 kind, varint length), index
(ix * nz + iz) * ny + iy.

Layout (docs/SKIFF_PLAN.md): the open fore deck, with the storage corner under the canvas lean-to at the bow
and the grated hatch over the hold's ladder; the cabin at the stern (its common room with the stair down to
the hold, the bedroom aft of it behind a door, a window in each side); the pilot deck on the cabin's roof,
reached by the crate stair on the starboard side of the fore deck, with the wheel, under the canvas roof;
the long, low storage hold under the decks.
"""
import math
import struct
from collections import deque

import numpy as np

import skiff_shape as ss

OUT, SOLID, DRY, LADDER, AIRLOCK, WINDOW, FURNITURE, DOOR = 0, 1, 2, 3, 4, 5, 6, 16

CELL = ss.CELL
X0, X1 = -5.5, 5.5
Y0, Y1 = -4.5, 7.5
Z0, Z1 = -14.0, 14.0

M0 = ss.DECK_Y               # the fore deck, the cabin floor
PY = ss.PILOT_Y              # the pilot deck
HO = ss.HOLD_Y               # the hold floor
SLAB = ss.DECK_SLAB
CF = ss.CABIN_FRONT_Z        # outer face of the cabin's front wall (the wall cells: CF - 0.5 .. CF)
PART = ss.PARTITION_Z        # the partition between the common room and the bedroom (cells PART +- 0.25)


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


# ---------------------------------------------------------------- rooms: (x0, x1, y0, y1, z0, z1), clipped to the hull
INF = 20.0
ROOMS = {
    "common_room": (-INF, INF, M0, PY - SLAB, PART + 0.25, CF - 0.5),
    "bedroom": (-INF, INF, M0, PY - SLAB, -INF, PART - 0.25),
    "hold": (-INF, INF, HO, M0 - SLAB, ss.HOLD_Z[0], ss.HOLD_Z[1]),
}

# doors: index -> (name, box). 2 blocks wide (two leaves) and 2 high in the walls; the hatch lies flat
DOORS = {
    0: ("cabin", (-1.0, 1.0, M0, M0 + 2.0, CF - 0.5, CF)),
    1: ("bedroom", (-2.0, 0.0, M0, M0 + 2.0, PART - 0.25, PART + 0.25)),   # to starboard of the hold stair's rail
    2: ("grate", (-0.5, 0.5, M0 - SLAB, M0, 1.5, 2.5)),
}
CABIN_DOOR, BEDROOM_DOOR, GRATE_HATCH = 0, 1, 2

# the ladder under the grated hatch of the fore deck, down to the hold's floor
LADDERS = {
    "grate": (-0.5, 0.5, HO, M0 - SLAB, 1.5, 2.5),
}

# stairs: (name, x0, x1, z_start, direction (+1: climbs towards the bow), y_start, steps); each step is 0.5 high and
# 0.5 deep, the first step's top at y_start + 0.5 (going up) or y_start - 0.5 (going down)
STAIRS = (
    ("pilot", -3.5, -2.0, 0.0, -1, M0, +6),       # fore deck -> pilot deck, crate steps climbing aft along the starboard side
    ("hold", 0.0, 1.5, -4.5, -1, M0, -4),          # common room -> hold, going down aft
)
HOLD_HOLE = (0.0, 1.5, -7.5, -4.5)      # opening in the cabin floor over the hold stair (x0, x1, z0, z1)
WINDOWS = ((-11.0, -9.5, 1.0, 2.0), (-6.0, -4.5, 1.0, 2.0))   # (z0, z1, y0, y1): the bedroom's and the common room's windows, both sides
HELM_BOX = (-0.5, 0.5, PY, PY + 1.0, -4.5, -4.0)
KING_POST = (-0.5, 0.5, PY, PY + 3.5, ss.CANOPY_Z - 0.5, ss.CANOPY_Z + 0.5)
POLE_H = 3.5            # the corner poles' feet are solid this high above the pilot deck
PILOT_RAIL_GAP = (-3.5, -2.0)   # the front balustrade of the pilot deck is open over the crate stair

FACES = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))


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


def pilot_plan(x, z):
    """Is (x, z) on the pilot deck (the cabin roof and its overhang)?"""
    return abs(x) <= ss.PILOT_HW and ss.PILOT_Z[0] <= z <= ss.PILOT_Z[1]


def build():
    g = Grid()
    X, Y, Z = g.X, g.Y, g.Z
    # ---- hull: solid planking and decks; open air above the fore deck; the cabin walls up to the pilot deck
    hx = _vec(ss.hull_x, Z, np.minimum(Y, ss.PILOT_Y))
    keel = _vec(ss.keel_y, Z)
    sheer = _vec(ss.sheer_y, Z)
    body = (np.abs(X) <= hx) & (Y >= keel) & (Y <= sheer) & (hx > 0.2)
    g.k[body] = SOLID
    inner = body & (np.abs(X) <= hx - ss.SHELL) & (Y >= keel + ss.SHELL)
    fore = Z > CF
    floor = _vec(ss.deck_y, Z)
    g.k[inner & fore & (Y > floor)] = OUT
    # the pilot deck: its slab over the cabin and its overhang beyond the hull sides and the cabin's front wall
    plan2d = np.zeros((g.nx, g.nz), dtype=bool)
    for i in range(g.nx):
        for l in range(g.nz):
            plan2d[i, l] = pilot_plan(g.xs[i], g.zs[l])
    slab = (g.ys > PY - SLAB) & (g.ys < PY)
    g.k[plan2d[:, None, :] & slab[None, :, None]] = SOLID
    # its balustrade: the outermost ring of cells, a block high (open over the crate stair)
    inner2d = plan2d.copy()
    inner2d[1:, :] &= plan2d[:-1, :]
    inner2d[:-1, :] &= plan2d[1:, :]
    inner2d[:, 1:] &= plan2d[:, :-1]
    inner2d[:, :-1] &= plan2d[:, 1:]
    edge2d = plan2d & ~inner2d
    rail = (g.ys > PY) & (g.ys < PY + ss.RAIL_H)
    g.k[edge2d[:, None, :] & rail[None, :, None]] = FURNITURE
    # ---- rooms: inside the hull with a solid cell between them and the outside across every face
    enclosed = inner.copy()
    for o in FACES:
        enclosed &= np.roll(body, o, axis=(0, 1, 2))
    for name, box in ROOMS.items():
        g.set(DRY, *box, where=enclosed)
    # the partition between the common room and the bedroom
    g.set(SOLID, -INF, INF, M0, PY - SLAB, PART - 0.25, PART + 0.25, where=inner)
    # the bedroom's windows (glass in the side walls)
    for z0, z1, y0, y1 in WINDOWS:
        g.set(WINDOW, -INF, INF, y0, y1, z0, z1, where=body & ~inner & (Z < CF - 0.5))
    # ---- stairs (steps are furniture: drawn by the model, not by the room surfaces)
    hole = HOLD_HOLE
    g.set(DRY, hole[0], hole[1], M0 - SLAB, M0, hole[2], hole[3])
    for st in STAIRS:
        steps = stair_steps(st)
        for x0, x1, z0, z1, top in steps:
            if st[6] > 0:
                g.set(FURNITURE, x0, x1, st[5], top, z0, z1)   # crate steps, solid down to the deck
            else:
                g.set(FURNITURE, x0, x1, top - 0.5, top, z0, z1)
    # the gap in the pilot deck's front balustrade at the top of the crate stair
    g.set(OUT, PILOT_RAIL_GAP[0], PILOT_RAIL_GAP[1], PY, PY + ss.RAIL_H, ss.PILOT_Z[1] - 0.6, ss.PILOT_Z[1] + 0.1)
    # rails round the hold stair's opening in the common room (not at its fore end, where one goes down)
    g.set(FURNITURE, hole[0] - 0.5, hole[0], M0, M0 + 1.0, hole[2] - 0.5, hole[3])
    g.set(FURNITURE, hole[1], hole[1] + 0.5, M0, M0 + 1.0, hole[2] - 0.5, hole[3], where=inner)
    if hole[2] - 0.5 > PART + 0.25 - 1e-6:   # (when the opening reaches the partition, the partition closes it)
        g.set(FURNITURE, hole[0] - 0.5, hole[1] + 0.5, M0, M0 + 1.0, hole[2] - 0.5, hole[2], where=inner)
    # ---- the pilot deck's fittings: the corner poles' feet, the king post of the canvas roof, the helm
    for fx, fz in ss.POLE_FEET:
        for sx in (1, -1):
            x = sx * fx
            g.set(FURNITURE, x - 0.25, x + 0.25, PY, PY + POLE_H, fz - 0.25, fz + 0.25)
    g.set(FURNITURE, *KING_POST)
    for fx, fz in ss.PILLARS:
        for sx in (1, -1):
            g.set(FURNITURE, sx * fx - 0.25, sx * fx + 0.25, PY, PY + POLE_H, fz - 0.25, fz + 0.25)
    (fx, fy, fz), _ = ss.DERRICKS[0]
    for sx in (1, -1):
        g.set(FURNITURE, sx * fx - 0.25, sx * fx + 0.25, PY, PY + 1.5, fz - 0.25, fz + 0.25)
    g.set(FURNITURE, *HELM_BOX)
    for name, box in LADDERS.items():
        g.set(LADDER, *box)
    # ---- doors (after everything: they cut through walls and decks)
    for d, (name, box) in DOORS.items():
        g.set(DOOR + d, *box)
    return g


PLACES = {
    "fore_deck": (-INF, INF, M0, M0 + 0.4, CF, 8.0),
    "bow_corner": (-INF, INF, M0, M0 + 0.4, 8.0, INF),
    "pilot_deck": (-INF, INF, PY, PY + 0.4, -INF, INF),
}


def walkable_report(g, start=(0.0, M0 + 0.01, 4.0)):
    """Standing places (1 x 1 block footprint) reachable from the fore deck with every door open:
    returns (reached per room, total)."""
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
    places.update(PLACES)
    for name, (x0, x1, y0, y1, z0, z1) in places.items():
        cells = [(i, j, l) for (i, j, l) in seen
                 if x0 <= X0 + (i + 1) * CELL <= x1 and y0 - 0.1 <= Y0 + j * CELL <= y1 and z0 <= Z0 + (l + 1) * CELL <= z1]
        reached[name] = len(cells)
    return reached, len(seen)


def leaks(g):
    """Cells of the rooms (dry or ladder) that touch the outside air across a face: none, but the hold stair's
    opening (in the cabin, not the outside) and the ladder under the grate hatch."""
    k = g.k
    room = (k == DRY) | (k == LADDER)
    out = k == OUT
    touch = np.zeros_like(room)
    for o in FACES:
        touch |= np.roll(out, o, axis=(0, 1, 2))
    bad = room & touch
    return [(float(g.xs[i]), float(g.ys[j]), float(g.zs[l])) for i, j, l in zip(*np.nonzero(bad))]


GRID_PATH = "src/main/resources/assets/medievalships/interiors/rustic_skiff.grid"

if __name__ == "__main__":
    g = build()
    counts = {int(k): int((g.k == k).sum()) for k in np.unique(g.k)}
    print("grid", g.nx, g.ny, g.nz, "cells", counts)
    lk = leaks(g)
    print("room cells open on the outside:", len(lk), lk[:10])
    reached, total = walkable_report(g)
    print("standing places reached from the fore deck (doors open):", total)
    for name, n in reached.items():
        print("  %-16s %s" % (name, n if n else "UNREACHABLE"))
