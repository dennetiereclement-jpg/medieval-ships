"""Interior grid of the Gear Steamship: what is solid, dry, a ladder, a door... in 0.5 block cells.

Same format and cell kinds as tools/frigate_interior.py (read by fr.medievalships.core.InteriorGrid): the
grid gives the collisions of the hull, the decks, the bulwarks, the walls, the stairs, the ladders and the
doors, the dry rooms and the volume where the players are carried. The model generator
(tools/generate_gear_steam.py) draws the walls, floors and ceilings of the rooms on the boundaries of these
cells, so what is drawn is what collides.

  src/main/resources/assets/medievalships/interiors/gear_steamship.grid

Layout (docs/GearSteam_PLAN.md):
  waist (main deck 4.5, z 5 -> 11.5): open, between the engine house and the forecastle; the companion
    down to the hold (port), the stairs up to the forecastle (both sides), the ladders up to the engine
    house roof on its front wall (both sides)
  engine room (4.5, z -6.5 -> 5): inside the engine house, 4 blocks high, the boiler under the funnel,
    a stair down to the hold (starboard); doors forward (waist) and aft (crew quarters)
  crew quarters (4.5, under the poop deck): door aft onto the stern gallery (a balcony over the counter)
  captain's cabin (7.5): the deckhouse on the poop deck, door aft; its fore part stands on the engine house
    roof and wraps the funnel (solid casing, the cabin's front wall); the bridge (11.0) on its roof, with
    the helm right behind the funnel, reached by a ladder on its aft wall; the poop deck (7.5) reached
    from the engine house roof (9.0) by three steps down on each side
  hold (1.0): the lower deck, one long room under the waist, the engine room and the crew quarters
"""
import math
import os
import struct
from collections import deque

import numpy as np

import gear_steam_shape as gs

OUT, SOLID, DRY, LADDER, AIRLOCK, WINDOW, FURNITURE, DOOR = 0, 1, 2, 3, 4, 5, 6, 16

CELL = gs.CELL
X0, X1 = -6.0, 6.0
Y0, Y1 = -3.5, 14.0
Z0, Z1 = -23.0, 23.0

M = gs.MAIN_DECK_Y          # 4.0
H = gs.HOLD_FLOOR_Y         # 0.5
P = gs.POOP_Y               # 7.0
F = gs.FORECASTLE_Y         # 5.5
E = gs.ENGINE_ROOF_Y        # 8.5
B = gs.BRIDGE_Y             # 10.5
S = gs.SLAB
DZ0, DZ1 = gs.DECKHOUSE_Z
DH = gs.DECKHOUSE_HALF

# rooms: (x0, x1, y0, y1, z0, z1), clipped to the inside of the hull (one cell of plating)
ROOMS = {
    "hold": (-4.5, 4.5, H, M - S, -15.5, 15.0),
    "engine_room": (-4.5, 4.5, M, E - S, gs.POOP_FRONT_Z + 0.5, gs.ENGINE_FRONT_Z - 0.5),
    "crew": (-4.5, 4.5, M, P - S, gs.TRANSOM_Z + 0.5, gs.POOP_FRONT_Z - 0.5),
    "cabin": (-DH + 0.5, DH - 0.5, P, B - S, DZ0 + 0.5, gs.CABIN_FRONT_Z),
}
# the stern gallery: an open balcony beyond the transom (floor = the main deck)
GALLERY = (-3.0, 3.0, M, gs.GALLERY_BULWARK_TOP, gs.GALLERY_Z, gs.TRANSOM_Z)
# doors: index -> (name, box); 2.0 wide (two leaves of 1.0), 2.5 tall where the room allows it (the engine room,
# the cabin), 2.0 under the 2.5 ceiling of the crew quarters (the crew and gallery doors). The box edges MUST lie on
# cell boundaries (multiples of 0.5): Grid.sel keeps the cells whose centre is strictly inside, so an edge on a cell
# centre (1.28.0 and before: +-0.75, 2.25..3.75, -1.25..0.25) lost half a cell on each side and the "1.5 wide" doors
# were 1.0 wide openings in the game, impassable as soon as the ship was not heading along an axis (the collision
# boxes of the cells are world-aligned and grow with the heading). Checked by door_openings() and GearSteamShipTest.
ENGINE_DOOR, CREW_DOOR, GALLERY_DOOR, CABIN_DOOR = 0, 1, 2, 3
DOOR_WIDTH = 2.0
DOORS = {
    ENGINE_DOOR: ("engine_room", (-1.0, 1.0, M, M + 2.5, gs.ENGINE_FRONT_Z - 0.5, gs.ENGINE_FRONT_Z)),
    CREW_DOOR: ("crew", (2.0, 4.0, M, M + 2.0, gs.POOP_FRONT_Z - 0.5, gs.POOP_FRONT_Z + 0.5)),   # port of the boiler
    GALLERY_DOOR: ("gallery", (-1.0, 1.0, M, M + 2.0, gs.TRANSOM_Z, gs.TRANSOM_Z + 0.5)),
    CABIN_DOOR: ("cabin", (-1.0, 1.0, P, P + 2.5, DZ0, DZ0 + 0.5)),
}
assert all(abs(v / CELL - round(v / CELL)) < 1e-9 for _, box in DOORS.values() for v in box), "door edges on cell boundaries"
# ladders (LADDER cells, climbed like a vanilla ladder): on the engine house front wall (both sides), up
# to its roof; on the deckhouse's aft wall, up to the bridge
LADDERS = {
    "roof_p": (gs.ROOF_LADDER_X[0], gs.ROOF_LADDER_X[1], M, E + 0.5, gs.ROOF_LADDER_Z[0], gs.ROOF_LADDER_Z[1]),
    "roof_s": (-gs.ROOF_LADDER_X[1], -gs.ROOF_LADDER_X[0], M, E + 0.5, gs.ROOF_LADDER_Z[0], gs.ROOF_LADDER_Z[1]),
    "bridge": (gs.BRIDGE_LADDER_X[0], gs.BRIDGE_LADDER_X[1], P, B + 0.5, gs.BRIDGE_LADDER_Z[0], gs.BRIDGE_LADDER_Z[1]),
}
# the masts (1 x 1 block columns, (z, foot)): the main mast stepped on the keel (through the hold and the
# waist), the mizzen on the poop deck
MASTS = [(gs.MAIN_MAST_Z, H - S), (gs.MIZZEN_Z, P)]
# the funnel through the engine house roof (round, drawn by the model; a square column in the grid)
FUNNEL = (-1.5, 1.5, E, Y1, gs.FUNNEL_Z - 1.5, gs.FUNNEL_Z + 1.5)
# the dome's drum on the engine house roof (solid)
DOME = (-3.0, 3.0, E, Y1, gs.DOME_Z - 3.0, gs.DOME_Z + 3.0)
# the crane's post on the poop deck
CRANE_POST = (-0.5, 0.5, P, 11.0, gs.CRANE_Z - 0.5, gs.CRANE_Z + 0.5)
# the boiler in the engine room, under the funnel (solid machinery)
BOILER = (-1.5, 1.5, M, E - S, gs.FUNNEL_Z - 0.4, gs.FUNNEL_Z + 2.0)


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
        hx = np.zeros(self.k.shape)
        for j, y in enumerate(ys):
            for l, z in enumerate(zs):
                if gs.TRANSOM_Z < z < gs.FORE_SCALE + 4.0:
                    hx[:, j, l] = gs.hull_x(z, y)
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


def deck_top(Z):
    """Height of the solid hull (the deck) at z: poop, engine house roof, waist, forecastle."""
    return np.where(Z < gs.POOP_FRONT_Z, P, np.where(Z < gs.ENGINE_FRONT_Z, E, np.where(Z < gs.FORECASTLE_Z, M, F)))


def bulwark_top(Z):
    return np.where(Z < gs.POOP_FRONT_Z, gs.POOP_BULWARK_TOP, np.where(Z < gs.ENGINE_FRONT_Z, gs.ENGINE_RAIL_TOP,
                    np.where(Z < gs.FORECASTLE_Z, gs.WAIST_BULWARK_TOP, gs.FORECASTLE_BULWARK_TOP)))


STEPS = {}   # name -> step boxes (for the model)


def build():
    g = Grid()
    hull = g.inside(0.0)
    inner = g.inside(0.5)
    X, Y, Z = g.X, g.Y, g.Z
    # the hull up to its deck at every z is solid; the rooms are carved out of it
    g.k[hull & (Y < deck_top(Z))] = SOLID
    # bulwarks: a shell 0.6 thick on the hull sides above the decks; the transom closes the stern
    shell = hull & (np.abs(X) > g.HX - 0.6)
    g.k[shell & (Y < bulwark_top(Z))] = SOLID
    g.k[hull & (Z < gs.TRANSOM_Z + 0.5) & (Y < gs.POOP_BULWARK_TOP)] = SOLID
    # the bow: the bulwark closes round the stem, the raised prow above it
    g.k[hull & (Z > gs.DECK_MAX_Z) & (Y < gs.FORECASTLE_BULWARK_TOP)] = SOLID
    g.set(SOLID, -0.5, 0.5, F, gs.STEM_HEAD[1], gs.DECK_MAX_Z - 0.5, gs.STEM_HEAD[2] + 0.5, where=hull | (Z > gs.DECK_MAX_Z))
    # the engine house roof railing across the step down to the waist (gaps at the ladders below)
    g.set(SOLID, -4.5, 4.5, E, gs.ENGINE_RAIL_TOP, gs.ENGINE_FRONT_Z - 0.5, gs.ENGINE_FRONT_Z, where=hull)
    # the forecastle's break: its rail across the front (gaps at the stairs below)
    g.set(SOLID, -4.5, 4.5, F, gs.FORECASTLE_BULWARK_TOP, gs.FORECASTLE_Z, gs.FORECASTLE_Z + 0.5, where=hull)
    # rooms
    for name, box in ROOMS.items():
        g.set(DRY, *box, where=inner)
    # close the rooms where the hull is thinner than a cell (the rising bottom at the ends): no open cell
    # may touch the sea below the main deck
    for _ in range(2):
        room = (g.k == DRY)
        near = np.zeros_like(room)
        near[1:, :, :] |= room[:-1, :, :]
        near[:-1, :, :] |= room[1:, :, :]
        near[:, 1:, :] |= room[:, :-1, :]
        near[:, :-1, :] |= room[:, 1:, :]
        near[:, :, 1:] |= room[:, :, :-1]
        near[:, :, :-1] |= room[:, :, 1:]
        g.k[near & (g.k == OUT) & (Y < M)] = SOLID
    # the captain's deckhouse on the poop deck: walls 0.5 thick, its roof is the bridge (railed)
    g.set(SOLID, -DH, DH, P, B, DZ0, DZ1, where=g.k != DRY)
    g.set(SOLID, -DH, DH, B, gs.BRIDGE_RAIL_TOP, DZ0, DZ1, where=(np.abs(X) > DH - 0.5) | (Z < DZ0 + 0.5) | (Z > gs.BRIDGE_FRONT_Z))
    # the stern gallery: floor, bulwarks round it (open above)
    gx0, gx1, gy0, gy1, gz0, gz1 = GALLERY
    g.set(SOLID, gx0 - 0.5, gx1 + 0.5, M - 1.5, M, gz0 - 0.5, gz1)
    # under it, the stepped counter (the rows of plates of the model) down to the water
    for z0, z1, yb in gs.skirt_rows(gz0):
        g.set(SOLID, gx0 - 0.5, gx1 + 0.5, yb, M - 1.5, z0, z1)
    g.set(SOLID, gx0 - 0.5, gx1 + 0.5, M, gy1, gz0 - 0.5, gz1, where=(np.abs(X) > gx1) | (Z < gz0))
    # the poop deck reaches aft over the gallery (its roof) to OVERHANG_Z, carried by posts at its aft corners,
    # with its bulwark round the overhang (the gallery's last block stands out beyond it, open to the sky); the
    # transom stops at the poop deck there (the deck runs on)
    oz = gs.OVERHANG_Z
    g.set(SOLID, gx0 - 0.5, gx1 + 0.5, P - S, P, oz, gz1)
    g.set(SOLID, gx0 - 0.5, gx1 + 0.5, P, gs.POOP_BULWARK_TOP, oz, gz1, where=(np.abs(X) > gx1) | (Z < oz + 0.5))
    for sx in (-1, 1):
        g.set(SOLID, min(sx * gx1, sx * (gx1 + 0.5)), max(sx * gx1, sx * (gx1 + 0.5)), M, P, oz, oz + 0.5)
    g.set(OUT, gx0, gx1, P, gs.POOP_BULWARK_TOP, gz1, gz1 + 0.5)
    # the waist's hatch and companion down to the hold (port), the stairs up to the forecastle (both sides)
    cx0, cx1 = gs.COMPANION_X
    g.set(DRY, cx0, cx1, M - S - 0.01, M + 0.01, gs.COMPANION_Z[0], gs.COMPANION_Z[1])
    STEPS["companion"] = stair(g, cx0, cx1, gs.COMPANION_Z[0], gs.COMPANION_Z[1], M, H)
    g.set(SOLID, cx1, 4.5, H - S, M - S, gs.COMPANION_Z[0], gs.COMPANION_Z[1], where=inner)   # between the stair and the hull
    for side in (1, -1):
        xa, xb = sorted((side * gs.FC_STAIR_X[0], side * gs.FC_STAIR_X[1]))
        n = int(round((F - M) / CELL))
        steps = []
        for k in range(1, n + 1):
            za = gs.FC_STAIR_Z[0] + (k - 1) * CELL
            g.set(SOLID, xa, xb, M - CELL, M + k * CELL, za, za + CELL)
            steps.append((xa, xb, M + k * CELL, za, za + CELL))
        g.set(OUT, xa, xb, F, gs.FORECASTLE_BULWARK_TOP, gs.FORECASTLE_Z, gs.FORECASTLE_Z + 0.5)   # gap in the break rail
        STEPS["forecastle_%s" % ("p" if side > 0 else "s")] = steps
    # the engine room's stair down to the hold (starboard), its hatch in the engine room floor
    ex0, ex1 = gs.ENGINE_STAIR_X
    g.set(DRY, ex0, ex1, M - S - 0.01, M + 0.01, gs.ENGINE_STAIR_Z[1], gs.ENGINE_STAIR_Z[0])
    STEPS["engine"] = stair(g, ex0, ex1, gs.ENGINE_STAIR_Z[0], gs.ENGINE_STAIR_Z[1], M, H)
    g.set(SOLID, -4.5, ex0, H - S, M - S, gs.ENGINE_STAIR_Z[1], gs.ENGINE_STAIR_Z[0], where=inner)
    # from the engine house roof down to the poop deck: three steps on each side deck, aft
    for side in (1, -1):
        xa, xb = sorted((side * gs.POOP_STEP_X[0], side * gs.POOP_STEP_X[1]))
        steps = []
        for k in range(1, 3):
            za = gs.POOP_FRONT_Z - k * CELL
            g.set(SOLID, xa, xb, P - CELL, E - k * CELL, za, za + CELL, where=inner)
            steps.append((xa, xb, E - k * CELL, za, za + CELL))
        STEPS["poop_%s" % ("p" if side > 0 else "s")] = steps
    # masts, funnel, dome drum, boiler
    for z, foot in MASTS:
        g.set(SOLID, -0.5, 0.5, foot, Y1, z - 0.5, z + 0.5)
    g.set(SOLID, *FUNNEL)
    g.set(SOLID, *DOME)
    g.set(FURNITURE, *BOILER)
    g.set(SOLID, *CRANE_POST)
    # ladders (and their gaps in the railings), doors
    for name, box in LADDERS.items():
        g.set(LADDER, *box)
    for x0, x1 in (gs.ROOF_LADDER_X, (-gs.ROOF_LADDER_X[1], -gs.ROOF_LADDER_X[0])):
        g.set(OUT, x0, x1, E, gs.ENGINE_RAIL_TOP, gs.ENGINE_FRONT_Z - 0.5, gs.ENGINE_FRONT_Z)
    g.set(OUT, gs.BRIDGE_LADDER_X[0], gs.BRIDGE_LADDER_X[1], B, gs.BRIDGE_RAIL_TOP, DZ0, DZ0 + 0.5)
    for d, (name, box) in DOORS.items():
        g.set(DOOR + d, *box)
    return g


def walkable_report(g, start=(-1.5, M + 0.01, 6.5)):
    """Standing places (1 x 1 block footprint) reachable from the waist, every door open, climbing the
    ladders: returns (reached per place, total)."""
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
    j0 = int(round((start[1] - Y0) / CELL))
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
    places = dict(ROOMS)
    places["waist"] = (-4.5, 4.5, M, M, gs.ENGINE_FRONT_Z, gs.FORECASTLE_Z)
    places["forecastle"] = (-4.5, 4.5, F, F, gs.FORECASTLE_Z, 22.0)
    places["engine_roof"] = (-4.5, 4.5, E, E, gs.POOP_FRONT_Z, gs.ENGINE_FRONT_Z)
    places["poop"] = (-4.5, 4.5, P, P, gs.TRANSOM_Z, gs.POOP_FRONT_Z)
    places["bridge"] = (-DH, DH, B, B, DZ0, DZ1)
    places["gallery"] = GALLERY[:3] + (M,) + GALLERY[4:]
    reached = {}
    for name, (x0, x1, y0, y1, z0, z1) in places.items():
        reached[name] = sum(1 for (i, j, l) in seen
                            if x0 <= X0 + (i + 1) * CELL <= x1 and abs(Y0 + j * CELL - y0) < 0.3 and z0 <= Z0 + (l + 1) * CELL <= z1)
    return reached, len(seen)


def door_openings(g):
    """The real opening of each door in the grid: index -> (x0, x1, y0, y1, z0, z1) covered by its DOOR cells
    (what the player can pass when it is open), to compare with DOORS."""
    out = {}
    for d in DOORS:
        m = g.k == DOOR + d
        if not m.any():
            out[d] = None
            continue
        h = CELL / 2
        out[d] = (float(g.X[m].min() - h), float(g.X[m].max() + h), float(g.Y[m].min() - h), float(g.Y[m].max() + h),
                  float(g.Z[m].min() - h), float(g.Z[m].max() + h))
    return out


GRID_PATH = "src/main/resources/assets/medievalships/interiors/gear_steamship.grid"

if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    g = build()
    size = g.write(os.path.join(root, GRID_PATH))
    counts = {int(k): int((g.k == k).sum()) for k in np.unique(g.k)}
    print("grid", g.nx, g.ny, g.nz, "bytes", size, "cells", counts)
    reached, total = walkable_report(g)
    print("standing places reached from the waist (doors open):", total)
    for name, n in reached.items():
        print("  %-14s %s" % (name, n if n else "UNREACHABLE"))
    for d, box in door_openings(g).items():
        name, want = DOORS[d]
        ok = box is not None and all(abs(a - b) < 1e-9 for a, b in zip(box, want))
        print("door %d %-12s opening %s %s" % (d, name, box, "" if ok else "DIFFERS FROM %s" % (want,)))
