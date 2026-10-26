package fr.medievalships.core;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.ArrayDeque;
import java.util.HashSet;
import java.util.Set;

import org.junit.jupiter.api.Test;

/**
 * The Crystal Airship: shape (same numbers as tools/crystal_shape.py), interior grid (decks, rooms connected by doors,
 * stairs and the ladder, windows, no way out through the hull, carry volume), seats and the helm, flight.
 */
class CrystalTest {
	private static final ShipType TYPE = Ships.CRYSTAL_AIRSHIP;
	private static final ShipGeometry G = TYPE.geometry();
	private static final InteriorGrid GRID = G.interior();
	private static final ShipPose ORIGIN = new ShipPose(0, 0, 0, 0);
	private static final InteriorGrid.State CLOSED = InteriorGrid.State.CLOSED;
	private static final double DT = 0.05;

	/** Values printed by {@code python3 tools/crystal_shape.py}. */
	@Test
	void matchesModelGenerator() {
		double[][] lobes = {
				{0, -8.200000, 0.884512}, {0, -0.300000, 1.000000}, {0, 12.340000, 0.622844},
				{1, 11.300000, 0.884512}, {1, 14.600000, 1.000000}, {1, 19.880000, 0.622844},
				{2, -16.300000, 0.884512}, {2, -12.000000, 1.000000}, {2, -5.120000, 0.622844}};
		for (double[] r : lobes) {
			assertEquals(r[2], CrystalLayout.lobeScale((int) r[0], r[1]), 1e-5, "lobe " + (int) r[0] + " at " + r[1]);
		}
		double[][] hull = {
				{-20.0, -3.0, 4.962613, -6.625835, 1.000000},
				{-10.0, -6.0, 4.985641, -9.900000, 1.000000},
				{0.0, -8.5, 2.508060, -9.000000, 1.000000},
				{0.0, 0.5, 5.998881, -9.000000, 1.000000},
				{8.0, -3.0, 5.260012, -7.221454, 1.000000},
				{16.0, -2.0, 4.305152, -5.574002, 3.000000},
				{22.0, 1.5, 2.975534, -2.810432, 3.000000},
				{-16.0, 2.0, 5.574560, -8.631093, 1.000000}};
		for (double[] r : hull) {
			assertEquals(r[2], CrystalLayout.hullX(r[0], r[1]), 1e-5, "hull half width at " + r[0] + ", " + r[1]);
			assertEquals(r[3], CrystalLayout.keelY(r[0]), 1e-5, "keel at " + r[0]);
			assertEquals(r[4], CrystalLayout.sheerY(r[0]), 1e-5, "sheer at " + r[0]);
		}
		assertEquals(2.232000, CrystalLayout.nacelleR(-22.0), 1e-5);
		assertEquals(2.785185, CrystalLayout.nacelleR(-15.0), 1e-5);
		assertEquals(1.833030, CrystalLayout.nacelleR(-10.0), 1e-5);
	}

	@Test
	void dimensions() {
		assertNotNull(GRID);
		assertTrue(G.flying());
		assertFalse(G.submarine());
		assertEquals(TYPE, Ships.byId("crystal_airship"));
		assertTrue(Ships.ALL.contains(TYPE));
		double length = CrystalLayout.BEAK_TIP_Z - CrystalLayout.tailEndZ();
		assertTrue(length > 50 && length < 56, "overall length " + length);
		assertEquals(48.6, CrystalLayout.BOW_Z - CrystalLayout.STERN_Z, 1e-9, "hull length");
		assertEquals(12.0, 2 * CrystalLayout.HULL_HW, 1e-9, "beam");
		double height = G.topY() - G.lowestY();
		assertTrue(height > 40 && height < 46, "overall height (mast and the crystal under the keel) " + height);
		// the balloon floats over the ring, the ring over the deck; the castle's roof clears the aft lobes
		assertTrue(CrystalLayout.RING_Y - CrystalLayout.RING_R > CrystalLayout.SHEER_WAIST, "the ring stands over the rail");
		assertTrue(CrystalLayout.CY - 6.6 >= CrystalLayout.RING_Y + CrystalLayout.RING_R - 0.01, "the ring's top under the balloon");
		assertFalse(CrystalLayout.insideBalloon(0, CrystalLayout.ROOF_TOP + 0.5, -18), "the roof clears the balloon");
		assertTrue(CrystalLayout.insideBalloon(0, CrystalLayout.CY, 0) && CrystalLayout.insideBalloon(5.9, CrystalLayout.CY + 1.1, 9.6));
		assertTrue(G.boundingRadius() >= CrystalLayout.BEAK_TIP_Z);
		assertTrue(G.aiReach() >= CrystalLayout.BEAK_TIP_Z && G.aiBack() >= -CrystalLayout.tailEndZ() - 1e-9);
		ShipConfig cfg = TYPE.defaults().get();
		ShipConfig lev = Ships.SKY_LEVIATHAN.defaults().get();
		assertNotNull(cfg.flight);
		assertTrue(cfg.acceleration < lev.acceleration && cfg.normalSpeed < lev.normalSpeed && cfg.maxTurnRate < lev.maxTurnRate,
				"heavier and slower than the Sky Leviathan");
		assertTrue(cfg.flight.climbSpeed < lev.flight.climbSpeed, "climbs slower than the Sky Leviathan");
		assertTrue(G.probes().size() > 300 && G.probes().size() < 1000, "probes " + G.probes().size());
	}

	/** Probes cover the whole volume: the balloon, the nacelles, the mast, the crystal under the keel, both ends. */
	@Test
	void probesCoverTheWholeAirship() {
		double minX = 0, maxX = 0, minY = 0, maxY = 0, minZ = 0, maxZ = 0;
		for (double[] p : G.probes()) {
			minX = Math.min(minX, p[0]);
			maxX = Math.max(maxX, p[0]);
			minY = Math.min(minY, p[1]);
			maxY = Math.max(maxY, p[1]);
			minZ = Math.min(minZ, p[2]);
			maxZ = Math.max(maxZ, p[2]);
		}
		assertTrue(maxX >= CrystalLayout.NACELLE[0] + CrystalLayout.NACELLE[4] - 0.3 && minX <= -(CrystalLayout.NACELLE[0] + CrystalLayout.NACELLE[4] - 0.3),
				"nacelles " + minX + " " + maxX);
		assertTrue(maxY >= CrystalLayout.MAST_TOP, "mast " + maxY);
		assertTrue(minY <= CrystalLayout.BOTTOM_CRYSTAL[3] + 0.05, "crystal under the keel " + minY);
		assertTrue(maxZ >= CrystalLayout.BEAK_TIP_Z - 0.01 && minZ <= CrystalLayout.tailEndZ() + 0.7, "ends " + minZ + " " + maxZ);
		assertTrue(G.aiHalfWidth() >= maxX, "the autopilot's clearance covers the width");
	}

	@Test
	void seatsAndHelm() {
		ShipGeometry.Seat pilot = G.seats().get(ShipGeometry.PILOT_SEAT);
		assertTrue(pilot.pilot());
		assertTrue(G.seats().size() >= 30, "seats " + G.seats().size());
		// the pilot stands in the cockpit behind the wheel, free of the helm
		double y = pilot.y() - 0.28;
		assertEquals(CrystalLayout.L2_Y, y, 1e-9);
		assertEquals(y, floorUnder(pilot.x(), y, pilot.z()), 1e-9, "the cockpit's floor");
		assertTrue(fits(pilot.x(), y, pilot.z()), "room for the pilot");
		assertTrue(G.inCarryVolume(pilot.x(), y + 0.5, pilot.z()));
		for (ShipGeometry.Seat s : G.seats()) {
			double[] d = s.dismountLocal();
			assertTrue(fits(d[0], d[1] - 0.02, d[2]), "dismount of seat " + s.index() + " is free");
			assertEquals(d[1] - 0.02, floorUnder(d[0], d[1] - 0.02, d[2]), 0.51, "dismount of seat " + s.index() + " is on a floor");
			assertTrue(G.inCarryVolume(s.x(), s.y(), s.z()), "seat " + s.index() + " is carried");
		}
		// clicking the wheel from the pilot's place
		ShipGeometry.Pick p = G.pick(ORIGIN, 0, CrystalLayout.L2_Y + 1.6, CrystalLayout.PILOT_Z, 0, -0.2, 1, 5);
		assertNotNull(p);
		assertEquals(ShipGeometry.PickKind.HELM, p.kind());
	}

	// ------------------------------------------------------------------ walking

	private static double floorUnder(double x, double y, double z) {
		return floorUnder(x, y, z, CLOSED);
	}

	private static double floorUnder(double x, double y, double z, InteriorGrid.State state) {
		double[] top = {Double.NEGATIVE_INFINITY};
		G.collectBoxes(ORIGIN, state, x - 0.3, y - 3, z - 0.3, x + 0.3, y + 0.01, z + 0.3, (a, b, c, d, e, f) -> {
			if (e <= y + 0.01 && a < x + 0.3 && d > x - 0.3 && c < z + 0.3 && f > z - 0.3) {
				top[0] = Math.max(top[0], e);
			}
		});
		return top[0];
	}

	private static boolean fits(double x, double y, double z) {
		return fits(x, y, z, CLOSED);
	}

	private static boolean fits(double x, double y, double z, InteriorGrid.State state) {
		boolean[] hit = {false};
		G.collectBoxes(ORIGIN, state, x - 0.3, y + 0.01, z - 0.3, x + 0.3, y + 1.8, z + 0.3, (a, b, c, d, e, f) -> {
			if (a < x + 0.3 && d > x - 0.3 && b < y + 1.8 && e > y + 0.01 && c < z + 0.3 && f > z - 0.3) {
				hit[0] = true;
			}
		});
		return !hit[0];
	}

	private static void area(String name, double x0, double x1, double y, double z0, double z1) {
		for (double z = z0; z <= z1 + 1e-9; z += 0.7) {
			for (double x = x0; x <= x1 + 1e-9; x += 0.6) {
				assertEquals(y, floorUnder(x, y, z), 1e-9, name + ": floor at " + x + ", " + z);
				assertTrue(fits(x, y, z), name + ": head room at " + x + ", " + z);
				assertTrue(G.inCarryVolume(x, y + 0.5, z), name + ": carried at " + x + ", " + z);
				assertTrue(G.inCarryVolume(x, y + 1.6, z), name + ": carried (head) at " + x + ", " + z);
			}
		}
	}

	@Test
	void decksAndRooms() {
		double m = CrystalLayout.MAIN_DECK_Y, lo = CrystalLayout.LOUNGE_Y, c = CrystalLayout.L2_Y;
		area("main deck (fore)", -1.4, 0.6, m, 2.2, 8.5);
		area("main deck (aft)", -1.4, 1.4, m, -9.0, -2.8);
		area("forecastle", -1.0, 1.0, CrystalLayout.FORECASTLE_Y, 14.4, 19.0);
		area("terrace on the castle", -1.4, 1.4, CrystalLayout.L1_TOP, -13.6, -11.0);
		area("officers' mess (aisle)", -0.6, 0.6, m, -17.0, -11.2);
		area("officers' mess (by the stair)", 2.4, 2.6, m, -22.0, -18.5);
		area("cockpit (at the window)", -0.6, 0.6, c, -14.9, -14.9);
		area("cockpit (behind the helm)", -1.6, 1.6, c, -18.6, -17.4);
		area("cockpit (starboard)", -2.9, -2.9, c, -20.6, -15.0);
		area("lounge (aisle)", -0.2, 0.2, lo, -6.6, 9.6);
		area("lounge (middle)", -1.0, 1.6, lo, -0.6, 2.6);
		area("storeroom", -0.6, 0.6, lo, 10.9, 14.0);
		area("storeroom (sides)", -2.2, 2.2, lo, 13.4, 13.4);
		area("hold", -0.6, 0.6, CrystalLayout.HOLD_Y, -4.6, 1.8);
		area("engine room landing", -0.9, 0.9, lo, -10.1, -8.2);
		area("engine room floor", -1.6, 1.6, CrystalLayout.ENGINE_FLOOR_Y, -14.0, -11.4);
		assertFalse(fits(0, CrystalLayout.ENGINE_FLOOR_Y, CrystalLayout.ENGINE_Z), "the crystal engine is solid");
		assertFalse(fits(0, m, CrystalLayout.RING_Z), "the ring's pillar is solid");
		assertFalse(fits(0, c, CrystalLayout.HELM_Z), "the helm is solid");
		// outside: not carried, nothing to stand on
		assertFalse(G.inCarryVolume(0, -16, 0));
		assertFalse(G.inCarryVolume(14, 6, 0));
		assertTrue(GRID.solidAt(0, CrystalLayout.CY, 0, CLOSED), "the balloon is solid");
		assertTrue(GRID.solidAt(CrystalLayout.NACELLE[0], CrystalLayout.NACELLE[1], -18.0, CLOSED), "the nacelles are solid");
		assertEquals(Double.NEGATIVE_INFINITY, floorUnder(12.5, 3, 5), "beside the ship: open air");
	}

	@Test
	void doorsCloseTheRooms() {
		double[][] doors = { // door, x, y, z (in the doorway)
				{CrystalLayout.CASTLE_DOOR, 0, 0, -10.35}, {CrystalLayout.ENGINE_DOOR, 0, -4, -7.25}, {CrystalLayout.STORE_DOOR, 1.5, -4, 10.25}};
		for (double[] d : doors) {
			int k = (int) d[0];
			assertFalse(fits(d[1], d[2], d[3]), "closed door " + k);
			assertTrue(fits(d[1], d[2], d[3], CLOSED.withDoor(k, true)), "open door " + k);
		}
		// the hatch of the hold is walked on when closed
		assertEquals(CrystalLayout.LOUNGE_Y, floorUnder(2.5, CrystalLayout.LOUNGE_Y, -6.0), 1e-9);
		assertFalse(fits(2.5, CrystalLayout.LOUNGE_Y - 0.6, -6.0), "hatch closed");
		assertTrue(fits(2.5, CrystalLayout.LOUNGE_Y - 0.6, -6.0, CLOSED.withDoor(CrystalLayout.HOLD_HATCH, true)), "hatch open");
	}

	/** Glass: the cockpit's arched window and side windows, the lounge's windows are solid, but no wall is drawn there. */
	@Test
	void windows() {
		assertEquals(InteriorGrid.WINDOW, GRID.kind((int) ((0.25 - GRID.x0) / GRID.cell), (int) ((4.25 - GRID.y0) / GRID.cell),
				(int) ((-14.25 - GRID.z0) / GRID.cell)), "the cockpit's arched window");
		assertTrue(GRID.solidAt(0, 4.25, -14.25, CLOSED));
		int lounge = 0, cockpit = 0;
		for (int i = 0; i < GRID.nx; i++) {
			for (int j = 0; j < GRID.ny; j++) {
				for (int k = 0; k < GRID.nz; k++) {
					if (GRID.kind(i, j, k) == InteriorGrid.WINDOW) {
						double y = GRID.y0 + (j + 0.5) * GRID.cell;
						if (y < 0) {
							lounge++;
						} else {
							cockpit++;
						}
					}
				}
			}
		}
		assertTrue(lounge >= 40, "lounge windows " + lounge);
		assertTrue(cockpit >= 40, "cockpit windows " + cockpit);
	}

	/** Walks a stair one step at a time (0.5 high, 0.5 deep), checking the floor and the head room. */
	private static double walk(String name, double x, double y, double z0, double dz, int steps, double expected) {
		double z = z0;
		for (int i = 0; i < steps * 2 + 2; i++) {
			z += dz / 2;
			double f = floorUnder(x, y + 0.6, z);
			assertTrue(Math.abs(f - y) <= 0.5 + 1e-9, name + ": step at z " + z + ": " + f + " from " + y);
			y = f;
			assertTrue(fits(x, y, z), name + ": head room at z " + z + " (y " + y + ")");
		}
		assertEquals(expected, y, 1e-9, name + ": arrives");
		return y;
	}

	@Test
	void stairsAndLadder() {
		walk("forecastle stair (port)", 3.35, 0.0, 10.8, 0.5, 4, CrystalLayout.FORECASTLE_Y);
		walk("forecastle stair (starboard)", -3.35, 0.0, 10.8, 0.5, 4, CrystalLayout.FORECASTLE_Y);
		walk("mess -> cockpit", 3.65, 0.0, -14.5, -0.5, 7, CrystalLayout.L2_Y);
		walk("mess -> engine room landing", -3.65, 0.0, -15.6, 0.5, 9, CrystalLayout.LOUNGE_Y);
		walk("landing -> engine room floor", 2.75, CrystalLayout.LOUNGE_Y, -10.5, -0.5, 7, CrystalLayout.ENGINE_FLOOR_Y);
		InteriorGrid.State open = CLOSED.withDoor(CrystalLayout.HOLD_HATCH, true);
		for (double y = CrystalLayout.HOLD_Y + 0.25; y < CrystalLayout.LOUNGE_Y + 0.5; y += 0.5) {
			assertTrue(GRID.ladderAt(2.5, y, -6.0) || GRID.solidAt(2.5, y, -6.0, CLOSED), "hold ladder at " + y);
		}
		assertFalse(GRID.solidAt(2.5, CrystalLayout.LOUNGE_Y - 0.25, -6.0, open), "hatch open");
	}

	/**
	 * Every room is reached from the main deck by walking, climbing the stairs and the ladder with every door open
	 * (standing places of a 1 x 1 block footprint and 2 blocks of head room, as tools/crystal_interior.py checks).
	 */
	@Test
	void roomsAreConnected() {
		int nx = GRID.nx, ny = GRID.ny, nz = GRID.nz;
		boolean[] pass = new boolean[nx * ny * nz];
		boolean[] lad = new boolean[nx * ny * nz];
		for (int i = 0; i < nx; i++) {
			for (int j = 0; j < ny; j++) {
				for (int k = 0; k < nz; k++) {
					byte kind = GRID.kind(i, j, k);
					int idx = (i * ny + j) * nz + k;
					pass[idx] = kind == InteriorGrid.OUT || kind == InteriorGrid.DRY || kind == InteriorGrid.LADDER || kind >= InteriorGrid.DOOR;
					lad[idx] = kind == InteriorGrid.LADDER;
				}
			}
		}
		int[] start = {(int) ((-0.5 - GRID.x0) / GRID.cell), (int) ((0.01 - GRID.y0) / GRID.cell), (int) ((4.0 - GRID.z0) / GRID.cell)};
		Set<Long> seen = new HashSet<>();
		ArrayDeque<int[]> q = new ArrayDeque<>();
		assertTrue(stand(pass, lad, start[0], start[1], start[2]), "start on the main deck");
		q.add(start);
		seen.add(key(start[0], start[1], start[2]));
		while (!q.isEmpty()) {
			int[] c = q.poll();
			boolean onLadder = any(lad, c[0], c[1], c[2], 2, 2, 2);
			int[][] moves = {{1, 0}, {-1, 0}, {0, 1}, {0, -1}, {0, 0}};
			for (int[] mv : moves) {
				int[] dys = mv[0] != 0 || mv[1] != 0 ? new int[] {-1, 0, 1, -2, -3, -4, -5, -6} : new int[] {};
				if (onLadder) {
					dys = concat(dys, new int[] {1, -1});
				}
				for (int dy : dys) {
					int i = c[0] + mv[0], j = c[1] + dy, k = c[2] + mv[1];
					if (seen.contains(key(i, j, k)) || !stand(pass, lad, i, j, k)) {
						continue;
					}
					seen.add(key(i, j, k));
					q.add(new int[] {i, j, k});
				}
			}
		}
		double[][] places = { // name index, x, floor, z of a spot in each room
				{0, 0.0, CrystalLayout.MAIN_DECK_Y, -19.5}, {1, 0.0, CrystalLayout.L2_Y, -18.0}, {2, 0.0, CrystalLayout.LOUNGE_Y, 1.0},
				{3, 0.0, CrystalLayout.LOUNGE_Y, 12.0}, {4, 0.0, CrystalLayout.HOLD_Y, -1.0}, {5, 0.0, CrystalLayout.LOUNGE_Y, -9.0},
				{6, 0.0, CrystalLayout.ENGINE_FLOOR_Y, -12.5}, {7, 0.0, CrystalLayout.FORECASTLE_Y, 16.0}};
		String[] names = {"officers' mess", "cockpit", "lounge", "storeroom", "hold", "engine room landing", "engine room floor", "forecastle"};
		for (double[] p : places) {
			boolean reached = false;
			int j = (int) Math.round((p[2] - GRID.y0) / GRID.cell);
			for (int di = -3; di <= 3 && !reached; di++) {
				for (int dk = -3; dk <= 3 && !reached; dk++) {
					reached = seen.contains(key((int) ((p[1] - GRID.x0) / GRID.cell) + di, j, (int) ((p[3] - GRID.z0) / GRID.cell) + dk));
				}
			}
			assertTrue(reached, names[(int) p[0]] + " reached from the main deck");
		}
		assertTrue(seen.size() > 2500, "standing places " + seen.size());
	}

	private static long key(int i, int j, int k) {
		return ((long) i * 4096 + j) * 4096 + k;
	}

	private static int[] concat(int[] a, int[] b) {
		int[] out = java.util.Arrays.copyOf(a, a.length + b.length);
		System.arraycopy(b, 0, out, a.length, b.length);
		return out;
	}

	private static boolean any(boolean[] m, int i0, int j0, int k0, int di, int dj, int dk) {
		for (int i = i0; i < i0 + di; i++) {
			for (int j = j0; j < j0 + dj; j++) {
				for (int k = k0; k < k0 + dk; k++) {
					if (i >= 0 && j >= 0 && k >= 0 && i < GRID.nx && j < GRID.ny && k < GRID.nz && m[(i * GRID.ny + j) * GRID.nz + k]) {
						return true;
					}
				}
			}
		}
		return false;
	}

	private static boolean stand(boolean[] pass, boolean[] lad, int i, int j, int k) {
		if (i < 0 || k < 0 || i + 1 >= GRID.nx || k + 1 >= GRID.nz || j < 1 || j + 4 > GRID.ny) {
			return false;
		}
		for (int a = i; a < i + 2; a++) {
			for (int b = j; b < j + 4; b++) {
				for (int c = k; c < k + 2; c++) {
					if (!pass[(a * GRID.ny + b) * GRID.nz + c]) {
						return false;
					}
				}
			}
		}
		if (any(lad, i, j - 1, k, 2, 2, 2)) {
			return true;
		}
		for (int a = i; a < i + 2; a++) {
			for (int c = k; c < k + 2; c++) {
				if (!pass[(a * GRID.ny + j - 1) * GRID.nz + c]) {
					return true;
				}
			}
		}
		return false;
	}

	/**
	 * No room opens on the outside air: every dry or ladder cell is walled off from the outside across its six faces
	 * (the hull, the castle's walls, the windows' glass).
	 */
	@Test
	void noWayOut() {
		int[][] faces = {{1, 0, 0}, {-1, 0, 0}, {0, 1, 0}, {0, -1, 0}, {0, 0, 1}, {0, 0, -1}};
		int leaks = 0;
		String first = null;
		for (int i = 1; i < GRID.nx - 1; i++) {
			for (int j = 1; j < GRID.ny - 1; j++) {
				for (int k = 1; k < GRID.nz - 1; k++) {
					byte kind = GRID.kind(i, j, k);
					if (kind != InteriorGrid.DRY && kind != InteriorGrid.LADDER) {
						continue;
					}
					for (int[] f : faces) {
						if (GRID.kind(i + f[0], j + f[1], k + f[2]) == InteriorGrid.OUT) {
							leaks++;
							if (first == null) {
								first = (GRID.x0 + (i + 0.5) * GRID.cell) + ", " + (GRID.y0 + (j + 0.5) * GRID.cell) + ", " + (GRID.z0 + (k + 0.5) * GRID.cell);
							}
						}
					}
				}
			}
		}
		assertEquals(0, leaks, "room cells open on the outside, first at " + first);
		assertFalse(fits(4.9, -2.0, 1.0), "the lounge's window glass stops a player");
		assertFalse(fits(0, 3.5, -14.25), "the cockpit's arched window stops a player");
	}

	@Test
	void gridFile() {
		int[] kinds = new int[256];
		for (int ix = 0; ix < GRID.nx; ix++) {
			for (int iz = 0; iz < GRID.nz; iz++) {
				for (int iy = 0; iy < GRID.ny; iy++) {
					kinds[GRID.kind(ix, iy, iz) & 0xFF]++;
				}
			}
		}
		assertTrue(kinds[InteriorGrid.SOLID] > 40000);
		assertTrue(kinds[InteriorGrid.DRY] > 10000);
		assertTrue(kinds[InteriorGrid.LADDER] > 10);
		for (int d : new int[] {0, 1, 2, 3}) {
			assertTrue(kinds[InteriorGrid.DOOR + d] > 0, "door " + d);
		}
		assertNotNull(G.decor());
		assertTrue(G.decor().seats().size() >= 30, "seats " + G.decor().seats().size());
		assertTrue(G.decor().blocks().size() >= 100, "furniture of the decoration mods " + G.decor().blocks().size());
		for (String mod : new String[] {"farmhouse_decorations:", "furnish:", "farmersdelight:", "landsoficaria:", "mebahelcreaturesdwarven:"}) {
			assertTrue(G.decor().blocks().stream().anyMatch(b -> b.block().startsWith(mod)), "uses " + mod);
		}
	}

	// ------------------------------------------------------------------ flight

	@Test
	void fliesSlowlyAndMajestically() {
		ShipConfig cfg = TYPE.defaults().get();
		ShipMover.Obstacles air = (x, y, z) -> y < 40;
		ShipPhysics physics = new ShipPhysics();
		Flight flight = new Flight();
		ShipPose pose = new ShipPose(0, 100, 0, 0);
		for (int i = 0; i < 200; i++) {
			pose = Flight.tick(G, pose, physics, flight, ShipPhysics.Controls.COAST, 0, cfg, air, DT).pose();
		}
		assertEquals(100, pose.y(), 1e-9, "hovers");
		for (int i = 0; i < 20; i++) {
			pose = Flight.tick(G, pose, physics, flight, ShipPhysics.Controls.COAST, cfg.flight.climbSpeed, cfg, air, DT).pose();
		}
		assertTrue(flight.vy < cfg.flight.climbSpeed * 0.5, "still gathering vertical speed after one second: " + flight.vy);
		for (int i = 0; i < 300; i++) {
			pose = Flight.tick(G, pose, physics, flight, ShipPhysics.Controls.COAST, cfg.flight.climbSpeed, cfg, air, DT).pose();
		}
		assertEquals(cfg.flight.climbSpeed, flight.vy, 1e-6);
		assertTrue(pose.y() > 110);
		for (int i = 0; i < 40; i++) {
			pose = Flight.tick(G, pose, physics, flight, new ShipPhysics.Controls(cfg.normalSpeed, 0), 0, cfg, air, DT).pose();
		}
		assertTrue(physics.speed > 0.2 && physics.speed < cfg.normalSpeed * 0.5, "speed after 2 s " + physics.speed);
		// it cannot come down into the ground: the crystal under the keel stops it
		ShipPose low = new ShipPose(0, 40 - G.lowestY() + 0.3, 0, 0);
		ShipPhysics p2 = new ShipPhysics();
		Flight f2 = new Flight();
		for (int i = 0; i < 100; i++) {
			low = Flight.tick(G, low, p2, f2, ShipPhysics.Controls.COAST, -cfg.flight.descendSpeed, cfg, air, DT).pose();
		}
		assertTrue(low.y() + G.lowestY() >= 39.9, "stopped above the ground: crystal at " + (low.y() + G.lowestY()));
	}
}
