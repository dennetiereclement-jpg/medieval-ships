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
WINDOW = 5     # glass in the hull: solid, dry, not drawn (the sea is seen through it)
FURNITURE = 6  # under a piece of furniture: solid, dry, not drawn (the furniture is)
DOOR = 16      # DOOR + k: door k (solid when closed, dry when open), k < 32

CELL = ns.CELL
X0, X1 = -8.0, 8.0
Y0, Y1 = -10.0, 16.0
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


# ---- layout (docs/NAUTILUS_PLAN.md, section 5): rooms in enfilade on the main level, the lower level,
# the double bottom, the wheelhouse and the projector cage on the casing. Boxes: (x0, x1, y0, y1, z0, z1).
M0, M1 = ns.MAIN_FLOOR_Y, ns.MAIN_FLOOR_Y + ns.LEVEL_HEIGHT          # main level: 0 .. 4.5
L0, L1 = ns.LOWER_FLOOR_Y, ns.MAIN_FLOOR_Y - 0.5                       # lower level: -4.5 .. -0.5
B0, B1 = ns.BILGE_FLOOR_Y, ns.LOWER_FLOOR_Y - 0.5                      # double bottom crawlway: -7 .. -5
SALON_TOP = 5.5

ROOMS = {
    # main level, bow to stern
    "corridor_fore": (-1.5, 1.5, M0, M1, 18.5, 26.5),
    "cabin_nemo":    (-5.0, -2.0, M0, M1, 20.0, 26.5),
    "cabin_aronnax": (2.0, 5.0, M0, M1, 20.0, 26.5),
    "dining":        (-5.0, 5.0, M0, M1, 13.0, 18.0),
    "library":       (-5.0, 5.0, M0, M1, 7.0, 12.5),
    "salon":         (-3.5, 3.5, M0, SALON_TOP, -6.5, 6.5),
    "stair_hall":    (-3.0, 2.5, L0, M1, -12.0, -7.0),
    "engine_room":   (-5.0, 5.0, L0, M1, -30.0, -12.5),
    # lower level
    "coursive":      (2.0, 4.8, L0, L1, 3.5, 24.5),
    "cross_fore":    (-1.5, 2.0, L0, L1, 22.5, 24.5),
    "airlock":       (-2.5, 2.5, L0, -1.0, 25.0, 29.0),
    "kitchen":       (-4.5, 1.5, L0, L1, 6.0, 14.0),
    "crew":          (-4.5, 1.5, L0, L1, 14.5, 22.0),
    "corridor_aft":  (-1.5, 1.5, L0, L1, -7.0, 5.5),
    "junction":      (-1.5, 4.8, L0, L1, 3.5, 5.5),
    "store_port":    (2.0, 4.8, L0, L1, -6.0, 3.0),
    "store_stbd":    (-4.8, -2.0, L0, L1, -6.0, 3.0),
    # double bottom: crawlway between the ballast tanks
    "crawlway":      (-1.5, 1.5, B0, B1, -12.0, 12.0),
    # on the casing
    "wheelhouse":    (-2.0, 2.0, ns.CASING_TOP_Y, ns.TOWER_TOP_Y - 0.5, ns.TOWER_Z[0] + 0.5, ns.TOWER_Z[1] - 0.5),
}

# doors: index -> (name, box). Doors are 2 blocks wide (two leaves), 2 high, as thick as the wall; hatches
# lie flat and stay 1 block
DOORS = {
    0: ("hatch", (0.0, 2.0, ns.CASING_TOP_Y - 0.5, ns.CASING_TOP_Y, -9.5, -7.5)),
    1: ("nemo", (-2.0, -1.5, M0, M0 + 2.0, 22.0, 24.0)),
    2: ("aronnax", (1.5, 2.0, M0, M0 + 2.0, 22.0, 24.0)),
    3: ("corridor_dining", (-1.0, 1.0, M0, M0 + 2.0, 18.0, 18.5)),
    4: ("dining_library", (-1.0, 1.0, M0, M0 + 2.0, 12.5, 13.0)),
    5: ("library_salon", (-1.0, 1.0, M0, M0 + 2.0, 6.5, 7.0)),
    6: ("salon_stairs", (1.5, 3.5, M0, M0 + 2.0, -7.0, -6.5)),
    7: ("stairs_engine", (1.0, 3.0, M0, M0 + 2.0, -12.5, -12.0)),
    8: ("airlock_inner", (-1.0, 1.0, L0, L0 + 2.0, 24.5, 25.0)),
    9: ("airlock_outer", None),  # in the hull at the end of the airlock tunnel, see build()
    11: ("wheelhouse_trap", (-1.0, 1.0, ns.CASING_TOP_Y - 0.5, ns.CASING_TOP_Y, 18.5, 20.0)),
    12: ("coursive_kitchen", (1.5, 2.0, L0, L0 + 2.0, 9.0, 11.0)),
    13: ("coursive_crew", (1.5, 2.0, L0, L0 + 2.0, 17.5, 19.5)),
    15: ("secret_trap", (-0.5, 0.5, L0 - 0.5, L0, 1.0, 2.0)),
    16: ("boat_hatch", (-0.5, 1.5, 7.5, 8.0, -19.5, -17.5)),
    17: ("store_port", (1.5, 2.0, L0, L0 + 2.0, -1.5, 0.5)),
    18: ("store_stbd", (-2.0, -1.5, L0, L0 + 2.0, -1.5, 0.5)),
}
HATCH_DOOR = 0
AIRLOCK_TUNNEL = (-7.0, -2.5, L0, L0 + 2.5, 26.0, 28.0)  # 2 blocks wide, 2.5 high

# ladders: (box, pillar box or None). The pillar gives something to push against at the bottom.
LADDERS = {
    "wheelhouse": ((-0.5, 0.5, M0, ns.CASING_TOP_Y + 0.5, 18.5, 19.5), (-0.5, 0.5, M0, ns.CASING_TOP_Y - 0.5, 19.5, 20.0)),
    "hatch":      ((1.0, 2.0, M0, ns.CASING_TOP_Y - 0.5, -9.0, -8.0), (1.0, 2.0, M0, ns.CASING_TOP_Y - 0.5, -9.5, -9.0)),  # pillar aft of it, up the shaft
    "boat":       ((0.5, 1.5, M0, 7.5, -19.0, -18.0), (0.5, 1.5, M0, 7.5, -18.0, -17.5)),
    "engine":     ((2.5, 3.5, L0, M0, -26.5, -25.5), (2.5, 3.5, L0, M0, -27.0, -26.5)),
    "bilge":      ((-0.5, 0.5, B0, L0, 1.0, 2.0), (-0.5, 0.5, B0, B1, 2.0, 2.5)),
}

# shafts round the ladders, from the ceiling of the room below to the hatch (2 x 2 blocks or so)
SHAFTS = [
    (0.0, 2.0, M1 - 0.5, ns.CASING_TOP_Y - 0.5, -9.5, -7.5),     # hatch to the casing
    (-1.0, 1.0, M1 - 0.5, ns.CASING_TOP_Y - 0.5, 18.5, 20.0),    # trap of the wheelhouse
    (-0.5, 1.5, M1 - 0.5, 7.5, -19.5, -17.5),                    # hatch of the lifeboat
]

# spiral staircase in the stair hall, lower level to main level, around a column
SPIRAL_CENTER = (-1.0, -9.5)
SPIRAL_R = (0.75, 2.0)
# catwalk along the engine room at the main level (the engine below), with a rail
CATWALK = (0.5, 4.0, M0 - 0.5, M0, -28.0, -12.5)
ENGINE_PARTITION_Z = (-21.5, -21.0)
BOAT_RECESS = (-1.5, 1.5, 8.0, 9.5, -23.0, -15.0)
TOWER_Z = ns.TOWER_Z
PILOT_Z = 20.6
HATCH_Z = (-9.0, -8.0)


def build():
    g = Grid()
    hull = g.inside(0.0)
    g.k[hull] = SOLID
    inner = g.inside(ns.SHELL)
    above_axis = g.Y > ns.AXIS_Y
    # raised casing along the top, the wheelhouse and the projector cage on it, the keels below
    cx = ns.CASING_HALF_WIDTH
    g.set(SOLID, -cx, cx, ns.AXIS_Y, ns.CASING_TOP_Y, *ns.CASING_Z, where=above_axis)
    tw = ns.TOWER_HALF_WIDTH
    g.set(SOLID, -tw, tw, ns.AXIS_Y, ns.TOWER_TOP_Y, *ns.TOWER_Z, where=above_axis)
    cw = ns.LAMP_CAGE_HALF_WIDTH
    g.set(SOLID, -cw, cw, ns.TOWER_TOP_Y, ns.LAMP_CAGE_TOP_Y - 0.3, *ns.LAMP_CAGE_Z)  # the projector lantern on the roof
    for z0, z1 in ns.KEELS:
        bottom = min(ns.hull_bottom(z0), ns.hull_bottom(z1))
        g.set(SOLID, -0.5, 0.5, bottom - ns.KEEL_DEPTH, ns.AXIS_Y, z0, z1, where=g.Y < ns.AXIS_Y)
    g.set(OUT, *BOAT_RECESS)
    # rooms (inside the pressure hull only; what is not a room stays solid: tanks, machinery, walls)
    for name, box in ROOMS.items():
        on_top = name == "wheelhouse"
        g.set(DRY, *box, where=None if on_top else inner)
    # great salon bay windows: round alcoves through the side walls down to the glass in the hull
    wz, wy, wr = ns.SALON_WINDOW
    disc = (g.Z - wz) ** 2 + (g.Y - wy) ** 2 < (wr - 0.25) ** 2
    g.k[disc & inner & (np.abs(g.X) > 3.0) & (g.k == SOLID)] = DRY
    g.k[disc & hull & ~inner & (np.abs(g.X) > 3.0)] = WINDOW
    # portholes of the lower coursive and of the cabins / rooms (tunnels to the glass in the hull)
    for z in ns.SMALL_WINDOWS_Z:
        port = (np.abs(g.Z - z) < 0.5) & (np.abs(g.Y - ns.SMALL_WINDOWS_Y) < 0.5) & inner & (g.k == SOLID)
        glass = (np.abs(g.Z - z) < 0.5) & (np.abs(g.Y - ns.SMALL_WINDOWS_Y) < 0.5) & hull & ~inner
        if ns.porthole_on(z, 1):
            g.k[port & (g.X > 3.5)] = DRY
            g.k[glass & (g.X > 3.5)] = WINDOW
        if ns.porthole_on(z, -1):
            g.k[port & (g.X < -4.0)] = DRY
            g.k[glass & (g.X < -3.5)] = WINDOW
    # portholes of the cabins on the main level
    for z, y in ns.CABIN_PORTHOLES:
        port = (np.abs(g.Z - z) < 0.5) & (np.abs(g.Y - y) < 0.5)
        g.k[port & inner & (g.k == SOLID) & (np.abs(g.X) > 4.5)] = DRY
        g.k[port & hull & ~inner & (np.abs(g.X) > 4.5)] = WINDOW
    # wheelhouse: four large windows, two ahead and one on each side; the projector lens at the front of the cage
    wy0, wy1 = ns.TOWER_WINDOWS_Y
    for x0, x1 in ns.TOWER_FRONT_WINDOWS_X:
        g.set(WINDOW, x0, x1, wy0, wy1, ns.TOWER_Z[1] - 0.5, ns.TOWER_Z[1])
    for x in (-ns.TOWER_HALF_WIDTH, ns.TOWER_HALF_WIDTH - 0.5):
        g.set(WINDOW, x, x + 0.5, wy0, wy1, *ns.TOWER_SIDE_WINDOW_Z)
    # spiral staircase: one turn from the lower floor to the main floor, a step every 1/9 turn
    scx, scz = SPIRAL_CENTER
    r = np.hypot(g.X - scx, g.Z - scz)
    ang = (np.degrees(np.arctan2(g.X - scx, g.Z - scz)) + 360.0) % 360.0  # 0 = towards +z (the entry), clockwise seen from above
    steps = int(round((M0 - L0) / CELL))
    ring = (r >= SPIRAL_R[0]) & (r < SPIRAL_R[1]) & (g.Z > -12.0) & (g.Z < -7.0)
    k = np.minimum(steps - 1, (ang / 360.0 * steps).astype(int))
    step_top = L0 + (k + 1) * CELL
    # each step a slab (room underneath for the turn below); steps and column are drawn as furniture
    # (tools/generate_nautilus.py spiral_stair), the cells only stop the players
    g.k[ring & (g.Y > step_top - 0.5) & (g.Y < step_top)] = FURNITURE
    g.k[(r < SPIRAL_R[0]) & (g.Y > L0 - 0.6) & (g.Y < M1) & (np.abs(g.Z - scz) < 1.0)] = FURNITURE  # the column
    # main level of the stair hall: a landing along the ladder side and towards the engine room
    g.set(SOLID, 1.0, 2.5, M0 - 0.5, M0, -12.0, -7.0)
    g.set(SOLID, -3.0, 3.5, M0 - 0.5, M0, -8.0, -7.0)  # gallery along the salon wall, from the top of the stairs
    # ... widening into a landing 2.5 blocks wide from the salon door to the engine room door
    g.set(SOLID, 2.5, 3.5, M0 - 0.5, M0, -12.0, -7.0)
    g.set(DRY, 2.5, 3.5, M0, M1, -12.0, -7.0)
    # engine room: catwalk with its rail, the partition between the batteries and the engine
    g.set(SOLID, *CATWALK)
    g.set(FURNITURE, CATWALK[0], CATWALK[0] + 0.5, M0, M0 + 1.0, CATWALK[4], CATWALK[5])  # its rail: drawn as a railing
    pz0, pz1 = ENGINE_PARTITION_Z
    g.set(SOLID, -5.0, 5.0, L0, M1, pz0, pz1, where=inner)
    g.set(DRY, 0.5, 2.5, L0, L0 + 2.5, pz0, pz1)        # walk-through below, beside the engine
    g.set(DRY, CATWALK[0] + 0.5, CATWALK[1], M0, M0 + 2.5, pz0, pz1)  # and along the catwalk
    # the shafts of the ladders through the hull, 2 blocks wide, up to the hatches
    for box in SHAFTS:
        g.set(DRY, *box)
    # ladders and their pillars
    for name, (box, pillar) in LADDERS.items():
        g.set(LADDER, *box)
        if pillar:
            g.set(SOLID, *pillar)
    # doors
    for d, (name, box) in DOORS.items():
        if box is not None:
            g.set(DOOR + d, *box)
    # airlock: its cells can be flooded; the tunnel through the hull ends at the outer door
    g.k[g.sel(*ROOMS["airlock"]) & (g.k == DRY)] = AIRLOCK
    tunnel = g.sel(*AIRLOCK_TUNNEL)
    g.k[tunnel & inner] = AIRLOCK
    g.k[tunnel & hull & ~inner] = DOOR + 9
    return g


def walkable_report(g, open_all=True):
    """Standing places (1 x 1 block footprint) reachable from the main corridor, with every door open:
    returns (reached, total) counts per room."""
    k = g.k
    passable = np.isin(k, (DRY, LADDER, AIRLOCK)) | ((k >= DOOR) if open_all else False)
    solid = ~passable & (k != OUT)  # walls, floors, furniture
    nx, ny, nz = k.shape
    # a standing spot: cell (i, j, l) with 2x2 footprint, solid below, 4 cells (2 blocks) of room above;
    # ladder cells count as standing spots (climbing)
    from collections import deque
    lad = k == LADDER

    def free(i, j, l):
        if i < 0 or l < 0 or i + 1 >= nx or l + 1 >= nz or j < 0 or j + 4 > ny:
            return False
        return passable[i:i + 2, j:j + 4, l:l + 2].all()

    def stand(i, j, l):
        if not free(i, j, l):
            return False
        if lad[i:i + 2, j, l:l + 2].any():
            return True
        return j > 0 and solid[i:i + 2, j - 1, l:l + 2].any()

    start = (g.at(0, 0.1, 22.0), )
    i0 = int((-0.5 - X0) / CELL)
    j0 = int((ns.MAIN_FLOOR_Y + 0.01 - Y0) / CELL)
    l0 = int((22.0 - Z0) / CELL)
    seen = set()
    q = deque()
    if stand(i0, j0, l0):
        q.append((i0, j0, l0))
        seen.add((i0, j0, l0))
    while q:
        i, j, l = q.popleft()
        onlad = lad[i:i + 2, j:j + 2, l:l + 2].any()
        for di, dl in ((1, 0), (-1, 0), (0, 1), (0, -1), (0, 0)):
            for dj in ((-1, 0, 1, 2) if (di or dl) else ()) + ((1, -1) if onlad else ()) + ((-1, -2, -3, -4, -5, -6) if (di or dl) else ()):
                n = (i + di, j + dj, l + dl)
                if n in seen:
                    continue
                if stand(*n):
                    seen.add(n)
                    q.append(n)
    reached = {}
    for name, (x0, x1, y0, y1, z0, z1) in ROOMS.items():
        cells = [(i, j, l) for (i, j, l) in seen
                 if x0 <= X0 + (i + 1) * CELL <= x1 and y0 - 0.1 <= Y0 + j * CELL <= y1 and z0 <= Z0 + (l + 1) * CELL <= z1]
        reached[name] = len(cells)
    return reached, len(seen)


GRID_PATH = "src/main/resources/assets/medievalships/interiors/nautilus.grid"

if __name__ == "__main__":
    import os
    import nautilus_decor
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    g = build()
    nautilus_decor.build()
    nautilus_decor.apply_to_grid(g)
    path = os.path.join(root, GRID_PATH)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    size = g.write(path)
    counts = {int(k): int((g.k == k).sum()) for k in np.unique(g.k)}
    print("grid", g.nx, g.ny, g.nz, "bytes", size, "cells", counts)
    reached, total = walkable_report(g)
    print("standing places reached from the fore corridor (doors open):", total)
    for name, n in reached.items():
        print("  %-14s %s" % (name, n if n else "UNREACHABLE"))
