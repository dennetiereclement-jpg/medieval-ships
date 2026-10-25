"""Interior grid of the Sky Leviathan: what is solid, dry, a ladder, a door... in 0.5 block cells.

The grid is the single source of the walkable volume: the mod reads it for the collisions of the
hull, the decks, the walls, the stairs, the balloon and its observation deck, for the ladders and
the doors, and for the volume where players are carried along; the model generator draws the walls,
floors and ceilings of the rooms on its boundaries, so what is drawn is what collides.

  src/main/resources/assets/medievalships/interiors/sky_leviathan.grid

Same file format as the Nautilus (tools/nautilus_interior.py): magic b"MSGRID1\\0", int32 nx, ny, nz,
float64 x0, y0, z0, float64 cell, then the cells in runs (uint8 kind, varint length), index
(ix * nz + iz) * ny + iy.

Layout (docs/LEVIATHAN_PLAN.md): the open main deck between the forecastle and the stern castle;
under the quarterdeck the captain's quarters (office and bedroom), under the poop the chart room,
under the forecastle the bosun's store; on the lower deck the common room, the corridor (coursive)
with the crew room and the storeroom on its sides; below them the hold; aft the engine room over two
levels with its boiler. A ladder in the central tower climbs from the main deck up through the
balloon to the observation deck on top of it.
"""
import math
import struct
from collections import deque

import numpy as np

import leviathan_shape as ls

OUT, SOLID, DRY, LADDER, AIRLOCK, WINDOW, FURNITURE, DOOR = 0, 1, 2, 3, 4, 5, 6, 16

CELL = ls.CELL
X0, X1 = -13.0, 13.0
Y0, Y1 = -7.0, 30.0
Z0, Z1 = -27.5, 26.5

M0 = ls.MAIN_DECK_Y            # main deck (open) and the main level under the castles
LO = -3.0                      # lower deck floor
HO = -5.5                      # hold floor
EO = -5.0                      # engine room floor (the hull is narrow lower down aft)
CASTLE = ls.QUARTERDECK_Y      # 3.0
POOP = ls.POOP_Y               # 5.5
SLAB = ls.DECK_SLAB


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
    # main level, under the castles
    "captain_office": (-INF, INF, M0, CASTLE - SLAB, -12.5, -8.0),
    "captain_bedroom": (-INF, INF, M0, CASTLE - SLAB, -INF, -13.0),
    "chart_room": (-INF, INF, CASTLE, POOP - SLAB, -INF, -15.5),
    "bosun_store": (-INF, INF, M0, CASTLE - SLAB, 9.5, INF),
    # lower deck
    "common_room": (-INF, INF, LO, M0 - SLAB, 1.0, INF),
    "coursive": (-1.0, 1.0, LO, M0 - SLAB, -9.0, 0.5),
    "crew_room": (-INF, -1.5, LO, M0 - SLAB, -8.5, 0.0),
    "storeroom": (1.5, INF, LO, M0 - SLAB, -8.5, 0.0),
    # hold and engine room
    "hold": (-INF, INF, HO, LO - SLAB, -9.0, 6.5),
    "engine_room": (-INF, INF, EO, M0 - SLAB, -16.5, -9.5),
}
# the top of the tower shaft and the observation deck are not rooms (open air)

# doors: index -> (name, box). 2 blocks wide (two leaves) and 2 high in the bulkheads; hatches lie flat
DOORS = {
    0: ("tower", (-ls.SHAFT_X, ls.SHAFT_X, M0, M0 + 2.0, ls.TOWER_Z[1] - 0.5, ls.TOWER_Z[1])),
    1: ("top_hatch", (-ls.SHAFT_X, ls.SHAFT_X, ls.TOP_DECK_Y - SLAB, ls.TOP_DECK_Y, ls.SHAFT_Z[0], ls.SHAFT_Z[1])),
    2: ("captain", (-1.0, 1.0, M0, M0 + 2.0, ls.QUARTERDECK_Z - 0.5, ls.QUARTERDECK_Z)),
    3: ("bedroom", (-1.0, 1.0, M0, M0 + 2.0, -13.0, -12.5)),
    4: ("chart_room", (-1.0, 1.0, CASTLE, CASTLE + 2.0, ls.POOP_Z - 0.5, ls.POOP_Z)),
    5: ("bosun_store", (-1.0, 1.0, M0, M0 + 2.0, ls.FORECASTLE_Z, ls.FORECASTLE_Z + 0.5)),
    6: ("common_room", (-1.0, 1.0, LO, LO + 2.0, 0.5, 1.0)),
    7: ("crew_room", (-1.5, -1.0, LO, LO + 2.0, -5.0, -3.0)),
    8: ("storeroom", (1.0, 1.5, LO, LO + 2.0, -5.0, -3.0)),
    9: ("engine_upper", (-1.0, 1.0, LO, LO + 2.0, -9.5, -9.0)),
    11: ("hold_hatch", (-0.5, 0.5, LO - SLAB, LO, -6.5, -5.5)),
}
TOWER_DOOR, TOP_HATCH = 0, 1

# ladders: tower shaft from the main deck to just above the observation deck, the hold ladder
LADDERS = {
    "tower": (-ls.SHAFT_X, ls.SHAFT_X, M0, ls.TOP_DECK_Y + 0.5, ls.SHAFT_Z[0], ls.SHAFT_Z[1]),
    "hold": (-0.5, 0.5, HO, LO - SLAB, -6.5, -5.5),
}

# stairs: (name, x0, x1, z_start, direction (+1: climbs towards the bow), y_start, steps); each step is
# 0.5 high and 0.5 deep, the first step's top at y_start + 0.5 (going up) or y_start - 0.5 (going down)
STAIRS = (
    ("qd_port", 2.5, 4.0, -4.5, -1, M0, +6),         # main deck -> quarterdeck, climbing aft
    ("qd_stbd", -4.0, -2.5, -4.5, -1, M0, +6),
    ("fc_port", 2.0, 3.5, 6.0, +1, M0, +6),           # main deck -> forecastle, climbing forward
    ("fc_stbd", -3.5, -2.0, 6.0, +1, M0, +6),
    ("poop", 2.0, 3.5, -12.5, -1, CASTLE, +5),        # quarterdeck -> poop, climbing aft
    ("companion", 1.5, 3.0, 4.5, -1, M0, -5),          # main deck -> common room, going down aft
    ("engine", 1.0, 2.5, -11.5, -1, LO, -4),           # landing -> engine room floor, going down aft
)
COMPANION_HOLE = (1.5, 3.0, 1.5, 4.5)       # opening in the main deck over the companion stair (x0, x1, z0, z1)
ENGINE_LANDING = (-11.5, -9.5)              # landing at the lower deck level inside the engine room (z)
BOILER = (0.0, -14.2, 1.2, EO, -1.0)        # x, z, radius (of its cells; the model is a little thinner), bottom, top
CHIMNEY_R = 0.45
HELM_BOX = (-0.5, 0.5, CASTLE, CASTLE + 1.0, -11.0, -10.5)


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


def build():
    g = Grid()
    X, Y, Z = g.X, g.Y, g.Z
    # ---- balloon (solid), the observation deck on it
    bw = _vec(ls.balloon_hw, Z)
    bh = _vec(ls.balloon_hh, Z)
    ok = (bw > 0.3) & (bh > 0.3)
    bw_, bh_ = np.where(ok, bw, 1.0), np.where(ok, bh, 1.0)
    balloon = ok & ((X / bw_) ** 2 + ((Y - ls.BALLOON_Y) / bh_) ** 2 <= 1.0)
    g.k[balloon] = SOLID
    half = _vec(ls.top_deck_half, Z)
    deck_plan = np.abs(X) < half
    g.k[deck_plan & (Y < ls.TOP_DECK_Y) & (Y > ls.BALLOON_Y)] = SOLID
    # its railing (one cell round the edge)
    plan2d = np.abs(g.xs[:, None]) < np.vectorize(ls.top_deck_half)(g.zs)[None, :]
    inner2d = plan2d.copy()
    inner2d[1:, :] &= plan2d[:-1, :]
    inner2d[:-1, :] &= plan2d[1:, :]
    inner2d[:, 1:] &= plan2d[:, :-1]
    inner2d[:, :-1] &= plan2d[:, 1:]
    edge2d = plan2d & ~inner2d
    layer = (g.ys > ls.TOP_DECK_Y) & (g.ys < ls.TOP_DECK_Y + 1.0)
    g.k[edge2d[:, None, :] & layer[None, :, None]] = FURNITURE
    # the flag mast on the deck
    g.set(FURNITURE, -0.25, 0.25, ls.TOP_DECK_Y, ls.TOP_DECK_Y + 2.5, ls.MAST_Z - 0.25, ls.MAST_Z + 0.25)

    # ---- hull: solid planking, decks; open air above the open decks; the balustrades of the castles
    hx = _vec(ls.hull_x, Z, Y)
    keel = _vec(ls.keel_y, Z)
    sheer = _vec(ls.sheer_y, Z)
    deck = _vec(ls.deck_y, Z)
    body = (np.abs(X) <= hx) & (Y >= keel) & (Y <= sheer) & (hx > 0.2)
    g.k[body] = SOLID
    inner = body & (np.abs(X) <= hx - ls.SHELL) & (Y >= keel + ls.SHELL)
    above_deck = inner & (Y > deck)
    g.k[above_deck] = OUT
    # balustrades of the castles: one cell inside the hull side, a block high
    hx_rail = _vec(ls.hull_x, Z, np.minimum(Y, ls.POOP_Y + 1.0))
    rail_zone = (hx_rail > 0.5) & (np.abs(X) <= hx_rail) & (np.abs(X) > hx_rail - CELL) & (Y > deck) & (Y < deck + 1.0) & (deck > M0)
    g.k[rail_zone & (Y > sheer)] = FURNITURE
    # the stern rail across the transom and the bow rail (fore end of the forecastle)
    for z0, z1, y in ((ls.HULL_STERN_Z, ls.HULL_STERN_Z + CELL + 0.01, POOP),):
        g.k[g.sel(-INF, INF, y, y + 1.0, z0 - 0.01, z1) & (np.abs(X) <= hx_rail)] = FURNITURE
    hx_c = _vec(ls.hull_x, Z, np.minimum(Y, ls.POOP_Y + 1.0))
    wide = (hx_c > 0.5) & (np.abs(X) <= hx_c - ls.SHELL)
    # ---- rooms
    for name, box in ROOMS.items():
        g.set(DRY, *box, where=inner)
    # bulkheads in front of the castles are walls (the rooms stop there), the rails on the castle edges
    for zc, y0, y1 in ((ls.QUARTERDECK_Z - 0.25, M0, CASTLE), (ls.FORECASTLE_Z + 0.25, M0, CASTLE), (ls.POOP_Z - 0.25, CASTLE, POOP)):
        g.set(SOLID, -INF, INF, y0, y1, zc - 0.25, zc + 0.25, where=inner)
        g.set(FURNITURE, -INF, INF, y1, y1 + 1.0, zc - 0.25, zc + 0.25, where=wide)
    # walls of the coursive and its side rooms
    for x in (-1.25, 1.25):
        g.set(SOLID, x - 0.25, x + 0.25, LO, M0 - SLAB, -9.0, 0.5)
    g.set(SOLID, -INF, INF, LO, M0 - SLAB, 0.0, 0.5, where=inner & (np.abs(X) > 1.0))
    g.set(SOLID, -INF, INF, LO, M0 - SLAB, -9.0, -8.5, where=inner & (np.abs(X) > 1.0))
    # ---- the engine room: landing at the lower deck level, its rail, the boiler
    g.set(SOLID, -INF, INF, LO - SLAB, LO, ENGINE_LANDING[0], ENGINE_LANDING[1], where=inner)
    bx, bz, br, b0, b1 = BOILER
    rr = np.hypot(X - bx, Z - bz)
    g.k[(rr < br) & (Y > b0) & (Y < b1)] = FURNITURE
    g.k[(rr < CHIMNEY_R) & (Y > b0) & (Y < M0 - SLAB)] = FURNITURE
    # ---- the central tower from the main deck to the balloon, its shaft and ladder through the balloon
    g.set(SOLID, -ls.TOWER_X, ls.TOWER_X, M0, ls.BALLOON_Y, ls.TOWER_Z[0], ls.TOWER_Z[1])
    for name, box in LADDERS.items():
        g.set(LADDER, *box)
    # ---- stairs (steps are furniture: drawn by the model, not by the room surfaces)
    hole = COMPANION_HOLE
    g.set(DRY, hole[0], hole[1], M0 - SLAB, M0, hole[2], hole[3])
    for st in STAIRS:
        steps = stair_steps(st)
        for x0, x1, z0, z1, top in steps:
            if st[6] > 0:
                g.set(FURNITURE, x0, x1, top - 0.5, top, z0, z1)
                # the steps' underside: open, or solid down to the deck below for the outside stairs
                g.set(FURNITURE, x0, x1, st[5], top, z0, z1)
            else:
                g.set(FURNITURE, x0, x1, top - 0.5, top, z0, z1)
        if st[6] > 0:
            # the gap in the castle rail at the top of the stair
            x0, x1, z0, z1, top = steps[-1]
            g.set(OUT, x0, x1, top, top + 1.0, z0 - 0.6, z1 + 0.6, where=g.k == FURNITURE)
    # rails round the companion opening on the main deck (not on its fore end, where one goes down)
    g.set(FURNITURE, hole[0] - 0.5, hole[0], M0, M0 + 1.0, hole[2] - 0.5, hole[3])
    g.set(FURNITURE, hole[1], hole[1] + 0.5, M0, M0 + 1.0, hole[2] - 0.5, hole[3])
    g.set(FURNITURE, hole[0] - 0.5, hole[1] + 0.5, M0, M0 + 1.0, hole[2] - 0.5, hole[2])
    # the engine room landing's rail (not over the stair)
    ez0, ez1 = ENGINE_LANDING
    st = [s for s in STAIRS if s[0] == "engine"][0]
    g.set(FURNITURE, -INF, st[1], LO, LO + 1.0, ez0, ez0 + 0.5, where=inner)
    g.set(FURNITURE, st[2], INF, LO, LO + 1.0, ez0, ez0 + 0.5, where=inner)
    # the helm
    g.set(FURNITURE, *HELM_BOX)
    # ---- doors (after everything: they cut through walls, decks and rails)
    for d, (name, box) in DOORS.items():
        g.set(DOOR + d, *box)
    return g


def walkable_report(g, start=(0.0, M0 + 0.01, 4.0)):
    """Standing places (1 x 1 block footprint) reachable from the main deck with every door open:
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
    places["main_deck"] = (-INF, INF, M0, M0 + 0.4, -7.5, 9.0)
    places["quarterdeck"] = (-INF, INF, CASTLE, CASTLE + 0.4, -15.0, -7.5)
    places["poop_deck"] = (-INF, INF, POOP, POOP + 0.4, -INF, -15.0)
    places["forecastle"] = (-INF, INF, CASTLE, CASTLE + 0.4, 9.0, INF)
    places["observation_deck"] = (-INF, INF, ls.TOP_DECK_Y, ls.TOP_DECK_Y + 0.4, -INF, INF)
    for name, (x0, x1, y0, y1, z0, z1) in places.items():
        cells = [(i, j, l) for (i, j, l) in seen
                 if x0 <= X0 + (i + 1) * CELL <= x1 and y0 - 0.1 <= Y0 + j * CELL <= y1 and z0 <= Z0 + (l + 1) * CELL <= z1]
        reached[name] = len(cells)
    return reached, len(seen)


GRID_PATH = "src/main/resources/assets/medievalships/interiors/sky_leviathan.grid"

if __name__ == "__main__":
    import os
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    g = build()
    counts = {int(k): int((g.k == k).sum()) for k in np.unique(g.k)}
    print("grid", g.nx, g.ny, g.nz, "cells", counts)
    reached, total = walkable_report(g)
    print("standing places reached from the main deck (doors open):", total)
    for name, n in reached.items():
        print("  %-16s %s" % (name, n if n else "UNREACHABLE"))
