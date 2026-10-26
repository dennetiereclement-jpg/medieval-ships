"""Interior grid of the Crystal Airship: what is solid, dry, a ladder, a window, a door... in 0.5 block cells.

The grid is the single source of the walkable volume: the mod reads it for the collisions of the hull, the
decks, the walls, the stairs, the stern castle, the balloon lobes and the engine nacelles, for the ladder and the
doors, and for the volume where players are carried along; the model generator draws the walls, floors and
ceilings of the rooms on its boundaries, so what is drawn is what collides.

  src/main/resources/assets/medievalships/interiors/crystal_airship.grid

Same file format as the Nautilus and the Sky Leviathan (magic b"MSGRID1\\0", int32 nx, ny, nz, float64 x0, y0,
z0, float64 cell, then the cells in runs (uint8 kind, varint length), index (ix * nz + iz) * ny + iy).

Layout (docs/CRYSTAL_PLAN.md): the open main deck and the forecastle; the stern castle with the officers' mess
(storey 1, on the main deck) and the cockpit (storey 2: the arched window facing the bow, the helm); under the
main deck the lounge (big windows on both sides) with the storeroom forward of it, the hold under the lounge, the
engine room aft over two levels (a landing at the lounge's level, the floor below).
"""
import math
import struct
from collections import deque

import numpy as np

import crystal_shape as cs

OUT, SOLID, DRY, LADDER, AIRLOCK, WINDOW, FURNITURE, DOOR = 0, 1, 2, 3, 4, 5, 6, 16

CELL = cs.CELL
X0, X1 = -12.5, 12.5
Y0, Y1 = -11.0, 26.0
Z0, Z1 = -26.5, 28.5

M0 = cs.MAIN_DECK_Y            # main deck, storey 1 of the castle
LO = -4.0                      # the lounge's deck (and the engine room's landing)
HO = -7.5                      # the hold's and the engine room's floor
FC = cs.FORECASTLE_Y           # 2.0
L2 = cs.L2_Y                   # 3.0: the cockpit
SLAB = cs.DECK_SLAB
CEIL_L1 = cs.L1_TOP - SLAB     # 2.5
CEIL_L2 = cs.L2_TOP - SLAB     # 6.0
CEIL_LO = M0 - SLAB            # -0.5
CEIL_HO = LO - SLAB            # -4.5
INF = 20.0

# ---------------------------------------------------------------- rooms: (x0, x1, y0, y1, z0, z1), clipped to the hull
STERN_IN = cs.STERN_Z + 0.5    # inner face of the stern wall
ROOMS = {
    "mess": (-INF, INF, M0, CEIL_L1, STERN_IN, cs.CASTLE_Z - 0.5),        # officers' mess (castle, storey 1)
    "cockpit": (-INF, INF, L2, CEIL_L2, STERN_IN, cs.L2_Z - 0.5),         # cockpit (castle, storey 2)
    "lounge": (-INF, INF, LO, CEIL_LO, -7.0, 10.0),
    "storeroom": (-INF, INF, LO, CEIL_LO, 10.5, 19.5),
    "engine_room": (-INF, INF, HO, CEIL_LO, -20.5, -7.5),
    "hold": (-INF, INF, HO, CEIL_HO, -6.5, 4.0),
}
WALKED = {   # the floors of the rooms (for the reports and the decor)
    "mess": M0, "cockpit": L2, "lounge": LO, "storeroom": LO, "engine_room": HO, "hold": HO,
}

# doors: index -> (name, box): 2 blocks wide (two leaves) and 2 high in the bulkheads; the hatch lies flat
CASTLE_DOOR, ENGINE_DOOR, STORE_DOOR, HOLD_HATCH = 0, 1, 2, 3
HATCH = (2.0, 3.0, -6.5, -5.5)     # x0, x1, z0, z1 of the hold hatch in the lounge's floor (its ladder under it)
DOORS = {
    CASTLE_DOOR: ("castle", (-1.0, 1.0, M0, M0 + 2.0, cs.CASTLE_Z - 0.5, cs.CASTLE_Z)),
    ENGINE_DOOR: ("engine_room", (-1.0, 1.0, LO, LO + 2.0, -7.5, -7.0)),
    STORE_DOOR: ("storeroom", (0.5, 2.5, LO, LO + 2.0, 10.0, 10.5)),
    HOLD_HATCH: ("hold_hatch", (HATCH[0], HATCH[1], LO - SLAB, LO, HATCH[2], HATCH[3])),
}

LADDERS = {
    "hold": (HATCH[0], HATCH[1], HO, LO + 0.5, HATCH[2], HATCH[3]),
}

# stairs: (name, x0, x1, z_start, direction (+1: climbs / goes towards the bow), y_start, steps (+ up, - down));
# each step is 0.5 high and 0.5 deep, the first step's top at y_start + 0.5 (going up) or y_start - 0.5 (going down)
STAIRS = (
    ("fc_port", 2.6, 4.1, 11.3, +1, M0, +4),          # main deck -> forecastle, climbing forward
    ("fc_stbd", -4.1, -2.6, 11.3, +1, M0, +4),
    ("cockpit", 2.9, 4.4, -15.0, -1, M0, +6),          # mess -> cockpit, climbing aft (port side)
    ("engine", -4.4, -2.9, -15.0, +1, M0, -8),         # mess -> engine room landing, going down forward (starboard)
    ("engine_floor", 2.0, 3.5, -11.0, -1, LO, -7),     # landing -> engine room floor, going down aft (port)
)
LANDING = (-11.0, -7.5)                       # the engine room's landing at the lounge's level (z)
ENGINE_HOLE = (-4.4, -2.9, -15.0, -12.5)      # opening in the mess's floor over the engine stair (x0, x1, z0, z1)
COCKPIT_HOLE = (2.9, 4.4, -18.0, -14.5)       # opening in the cockpit's floor over its stair
ENGINE = (0.0, -16.6, 2.0, HO, -3.6)          # the crystal engine: x, z, radius (of its cells), bottom, top
PLINTH = (-20.5, -18.6, HO + 1.0)             # z0, z1, top of the raised floor aft of the engine
HELM_BOX = (-0.6, 0.6, L2, L2 + 1.0, cs.HELM_Z - 0.3, cs.HELM_Z + 0.3)
# lantern posts on the main deck and the forecastle, the bow pennant's pole (x, floor, z)
POSTS = ((-2.2, M0, -9.4), (2.2, M0, -9.4), (-1.9, cs.FORECASTLE_Y, 15.2), (1.9, cs.FORECASTLE_Y, 15.2), (0.0, cs.FORECASTLE_Y, 23.4))
# the lounge's windows (z centre, half width) between y WIN_Y; the cockpit's side windows
LOUNGE_WINDOWS = ((-6.0, -4.0), (-3.0, -1.0), (0.0, 2.0), (3.0, 5.0), (6.0, 8.0))   # z spans (on cell boundaries)
WIN_Y = (-3.0, -1.0)
ROSE = (10.6, -0.35, 2.5)     # the bow's fan window (outside only): z of its centre, its flat top, radius
COCKPIT_WINDOWS = ((-18.0, -16.5), (-20.5, -19.0), (-22.5, -21.5))
COCKPIT_WIN_Y = (3.5, 5.5)

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


def ring_cells(g):
    """Cells of the golden ring (a torus in the ship's plane of symmetry) and its pedestal."""
    r = np.hypot(g.Y - cs.RING_Y, g.Z - cs.RING_Z)
    ring = (np.abs(g.X) < cs.RING_T / 2 + 0.2) & (r < cs.RING_R) & (r > cs.RING_R - cs.RING_W - 0.1)
    hw, top = cs.PEDESTAL
    ped = (np.abs(g.X) < hw) & (np.abs(g.Z - cs.RING_Z) < hw) & (g.Y > M0) & (g.Y < top + 0.3)
    return ring | ped


def build():
    g = Grid()
    X, Y, Z = g.X, g.Y, g.Z
    # ---- balloon lobes (solid), the mast on top
    bal = np.zeros(g.k.shape, dtype=bool)
    for lb in cs.LOBES:
        s = _vec(lambda z, lb=lb: cs.lobe_scale(lb, z), Z)
        ok = s > 0.05
        w = np.where(ok, lb[4] * s, 1.0)
        h = np.where(ok, lb[5] * s, 1.0)
        bal |= ok & (((X - lb[1]) / w) ** 2 + ((Y - lb[2]) / h) ** 2 <= 1.0)
    g.k[bal] = SOLID
    g.set(FURNITURE, -0.25, 0.25, cs.MAST_BASE - 0.5, Y1, cs.MAST_Z - 0.25, cs.MAST_Z + 0.25, where=g.k == OUT)

    # ---- engine nacelles, the stern engine (solid)
    nac = _vec(lambda x, y, z: 1.0 if cs.inside_nacelle(x, y, z) else 0.0, X, Y, Z) > 0.5
    g.k[nac] = SOLID
    ry, rz0, rz1, rr = cs.REAR_ENGINE
    g.k[(np.hypot(X, Y - ry) < rr) & (Z > rz1) & (Z < rz0 + 0.5)] = SOLID

    # ---- hull: solid planking, decks; open air above the open decks
    hx = _vec(cs.hull_x, Z, Y)
    keel = _vec(cs.keel_y, Z)
    sheer = _vec(cs.sheer_y, Z)
    deck = _vec(cs.deck_y, Z)
    body = (np.abs(X) <= hx) & (Y >= keel) & (Y <= sheer) & (hx > 0.2)
    g.k[body] = SOLID
    inner = body & (np.abs(X) <= hx - cs.SHELL) & (Y >= keel + cs.SHELL)
    above_deck = inner & (Y > deck)
    g.k[above_deck] = OUT
    # the bulwark rails: one cell inside the hull side, a block high above the open decks
    hx_rail = _vec(cs.hull_x, Z, np.minimum(Y, cs.SHEER_WAIST))
    rail = (hx_rail > 0.5) & (np.abs(X) <= hx_rail) & (np.abs(X) > hx_rail - CELL) & (Y > deck) & (Y < deck + cs.RAIL_H) & (Z > cs.CASTLE_Z)
    g.k[rail & (g.k == OUT)] = FURNITURE
    # ... round the bow of the forecastle (its foremost cells)
    hx_next = _vec(cs.hull_x, Z + CELL, np.minimum(Y, cs.SHEER_WAIST))
    bow_rail = (Z > cs.FORECASTLE_Z) & (hx_rail > 0.1) & (np.abs(X) <= hx_rail) & (np.abs(X) > hx_next - 0.05) & (Y > deck) & (Y < deck + cs.RAIL_H)
    g.k[bow_rail & (g.k == OUT)] = FURNITURE

    # ---- the stern castle: walls a cell thick, storey 1 on the main deck, storey 2 (the cockpit) aft of L2_Z
    cx = _vec(cs.castle_x, Z, Y)
    ctop = _vec(cs.castle_top, Z)
    castle = (Z > cs.STERN_Z) & (Z < cs.CASTLE_Z) & (np.abs(X) <= cx) & (Y > M0 - 0.01) & (Y < ctop)
    g.k[castle] = SOLID
    for (z0, z1, y0, y1) in ((STERN_IN, cs.CASTLE_Z - 0.5, M0, CEIL_L1), (STERN_IN, cs.L2_Z - 0.5, L2, CEIL_L2)):
        g.set(DRY, -INF, INF, y0, y1, z0, z1, where=castle & (np.abs(X) < cx - 0.5))
    # the terrace on storey 1's roof in front of the cockpit: its rail
    terrace = (Z > cs.L2_Z) & (Z < cs.CASTLE_Z) & (np.abs(X) <= cx)
    g.k[terrace & (Y > cs.L1_TOP) & (Y < cs.L1_TOP + cs.RAIL_H) & ((np.abs(X) > cx - 0.5) | (Z > cs.CASTLE_Z - 0.5))] = FURNITURE
    # the roof over the cockpit
    g.set(SOLID, -INF, INF, cs.L2_TOP - 0.01, cs.ROOF_Y[1] - 0.6, cs.ROOF_Z[0] + 0.4, cs.ROOF_Z[1], where=np.abs(X) < cx)

    # ---- rooms under the main deck: inside the hull with a solid cell between them and the outside across every
    # face, so no room opens on the air
    enclosed = inner.copy()
    for o in FACES:
        enclosed &= np.roll(body, o, axis=(0, 1, 2))
    for name in ("lounge", "storeroom", "engine_room", "hold"):
        g.set(DRY, *ROOMS[name], where=enclosed)
    # bulkheads: lounge | engine room, lounge | storeroom; the lounge's floor over the hold, the engine room's landing
    g.set(SOLID, -INF, INF, HO, CEIL_LO, -7.5, -7.0, where=inner)
    g.set(SOLID, -INF, INF, HO, CEIL_LO, 10.0, 10.5, where=inner)
    g.set(SOLID, -INF, INF, CEIL_HO, LO, -7.0, 10.0, where=inner)
    g.set(SOLID, -INF, INF, LO - SLAB, LO, LANDING[0], LANDING[1], where=inner)
    # the raised floor aft of the engine, the crystal engine
    pz0, pz1, ptop = PLINTH
    g.set(FURNITURE, -INF, INF, HO - 0.5, ptop, pz0, pz1, where=inner & (g.k == DRY))
    ex, ez, er, e0, e1 = ENGINE
    g.k[(np.hypot(X - ex, Z - ez) < er) & (Y > e0) & (Y < e1)] = FURNITURE

    # ---- the cockpit's arched window and side windows, the lounge's windows: glass (solid, seen through)
    ax, sill, spring, crown = cs.ARCH
    rad = (crown - spring)
    arch = (np.abs(X) < ax) & (Y > sill) & (Y < crown) & (Z > cs.L2_Z - 0.5) & (Z < cs.L2_Z) & (
        (Y < spring) | (((np.abs(X) / ax) ** 2 + ((Y - spring) / rad) ** 2) <= 1.0))
    g.k[arch & (g.k == SOLID)] = WINDOW
    for z0, z1 in COCKPIT_WINDOWS:
        g.set(WINDOW, -INF, INF, COCKPIT_WIN_Y[0], COCKPIT_WIN_Y[1], z0, z1, where=(g.k == SOLID) & castle & (np.abs(X) > cx - 0.55))
    hx_in = _vec(cs.hull_x, Z, Y)
    for z0, z1 in LOUNGE_WINDOWS:
        g.set(WINDOW, -INF, INF, WIN_Y[0], WIN_Y[1], z0, z1, where=(g.k == SOLID) & body & (np.abs(X) > 2.5))

    # ---- open decks: the turret, the ring and its pedestal, the crystal lamps at the castle's corners
    hw_t, tz0, tz1, ttop = cs.TURRET
    g.set(FURNITURE, -hw_t, hw_t, M0, ttop, tz0, tz1)
    g.k[ring_cells(g) & (g.k == OUT)] = FURNITURE
    for x, y, z in cs.CASTLE_CRYSTALS:
        g.set(FURNITURE, x - 0.3, x + 0.3, M0, y + 0.6, z - 0.3, z + 0.3, where=g.k == OUT)

    # the forecastle's rail across its front (gaps at the stairs, below)
    g.set(FURNITURE, -INF, INF, FC, FC + cs.RAIL_H, cs.FORECASTLE_Z, cs.FORECASTLE_Z + 0.5, where=(g.k == OUT) & (np.abs(X) < hx_rail))

    for x, y, z in POSTS:
        g.set(FURNITURE, x - 0.25, x + 0.25, y, y + 2.0, z - 0.25, z + 0.25, where=g.k == OUT)

    # ---- the ladder, the stairs (steps are furniture: drawn by the model, not by the room surfaces)
    for name, box in LADDERS.items():
        g.set(LADDER, *box)
    for x0, x1, z0, z1 in (ENGINE_HOLE, COCKPIT_HOLE):
        y = M0 if (x0, x1, z0, z1) == ENGINE_HOLE else L2
        g.set(DRY, x0, x1, y - SLAB, y, z0, z1)
    for st in STAIRS:
        steps = stair_steps(st)
        outside = st[0].startswith("fc_")
        for x0, x1, z0, z1, top in steps:
            g.set(FURNITURE, x0, x1, (st[5] if outside else top - 0.5), top, z0, z1)
        if outside:
            # the gap in the forecastle's rail at the top of the stair
            x0, x1, z0, z1, top = steps[-1]
            g.set(OUT, x0, x1, top, top + 1.0, z0 - 0.6, z1 + 0.6, where=g.k == FURNITURE)
    # rails round the openings of the stairs (not on the side one comes in by)
    x0, x1, z0, z1 = ENGINE_HOLE
    g.set(FURNITURE, x1, x1 + 0.5, M0, M0 + 1.0, z0, z1)                # inboard side (one goes in at the aft end)
    g.set(FURNITURE, x0, x1 + 0.5, M0, M0 + 1.0, z1, z1 + 0.5)          # fore end
    x0, x1, z0, z1 = COCKPIT_HOLE
    g.set(FURNITURE, x0 - 0.5, x0, L2, L2 + 1.0, z0, z1)                  # inboard side (one comes out at the aft end)
    # the landing's rail over the engine room (not over the two stairs)
    g.set(FURNITURE, -2.9, 2.0, LO, LO + 1.0, LANDING[0], LANDING[0] + 0.5, where=g.k == DRY)
    # the helm
    g.set(FURNITURE, *HELM_BOX)
    # ---- doors (after everything: they cut through walls, decks and rails)
    for d, (name, box) in DOORS.items():
        g.set(DOOR + d, *box)
    return g


def walkable_report(g, start=(0.0, M0 + 0.01, 4.0)):
    """Standing places (1 x 1 block footprint) reachable from the main deck with every door open:
    returns (reached per place, total)."""
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
        if lad[i:i + 2, max(0, j - 1):j + 1, l:l + 2].any():
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
    places = {name: (b[0], b[1], WALKED[name], WALKED[name] + 0.4, b[4], b[5]) for name, b in ROOMS.items()}
    places["engine_landing"] = (-INF, INF, LO, LO + 0.4, LANDING[0], LANDING[1])
    places["main_deck"] = (-INF, INF, M0, M0 + 0.4, cs.CASTLE_Z, cs.FORECASTLE_Z)
    places["forecastle"] = (-INF, INF, FC, FC + 0.4, cs.FORECASTLE_Z, INF)
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


GRID_PATH = "src/main/resources/assets/medievalships/interiors/crystal_airship.grid"

if __name__ == "__main__":
    import os
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    g = build()
    counts = {int(k): int((g.k == k).sum()) for k in np.unique(g.k)}
    print("grid", g.nx, g.ny, g.nz, "cells", counts)
    lk = leaks(g)
    print("room cells open on the outside:", len(lk), lk[:10])
    reached, total = walkable_report(g)
    print("standing places reached from the main deck (doors open):", total)
    for name, n in reached.items():
        print("  %-16s %s" % (name, n if n else "UNREACHABLE"))
