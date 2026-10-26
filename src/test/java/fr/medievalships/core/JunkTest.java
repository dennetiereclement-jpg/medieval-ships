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
 * The Dragon Junk: shape (same numbers as tools/junk_shape.py), interior grid (decks, rooms connected by doors, stairs
 * and the ladder, no way out through the hull, carry volume), seats, terrain probes over the whole vessel, flight.
 */
class JunkTest {
	private static final ShipType TYPE = Ships.DRAGON_JUNK;
	private static final ShipGeometry G = TYPE.geometry();
	private static final InteriorGrid GRID = G.interior();
	private static final ShipPose ORIGIN = new ShipPose(0, 0, 0, 0);
	private static final InteriorGrid.State CLOSED = InteriorGrid.State.CLOSED;
	private static final double DT = 0.05;
	private static final double M = JunkLayout.MAIN_DECK_Y, Q = JunkLayout.QUARTERDECK_Y, LO = JunkLayout.LOWER_DECK_Y,
			BR = JunkLayout.BEDROOM_Y;

	/** Values printed by {@code python3 tools/junk_shape.py} (see the commit of this test). */
	@Test
	void matchesModelGenerator() {
		double[][] keel = {{-19.0, -2.208333}, {-14.0, -4.05}, {-6.0, -4.5}, {15.0, -4.434896}, {21.0, -3.966682}};
		for (double[] r : keel) {
			assertEquals(r[1], JunkLayout.keelY(r[0]), 1e-5, "keel at " + r[0]);
		}
		double[][] hull = {{0.0, -3.5, 3.771208, 1.625514}, {0.0, -2.0, 4.369507, 1.625514}, {-16.0, -1.5, 4.091993, 2.5},
				{-16.0, -3.0, 2.861765, 2.5}, {15.0, -3.0, 3.331002, 1.0}, {18.5, -2.5, 1.515943, 1.0}, {20.5, -2.8, 0.651096, 1.0},
				{19.0, 0.5, 3.59604, 1.0}, {-18.0, 1.5, 3.959184, 2.5}, {-12.0, -4.0, 2.854173, 2.5}};
		for (double[] r : hull) {
			assertEquals(r[2], JunkLayout.hullX(r[0], r[1]), 1e-5, "hull half width at " + r[0] + ", " + r[1]);
			assertEquals(r[3], JunkLayout.sheerY(r[0]), 1e-5, "sheer at " + r[0]);
		}
		double[] roof = {5.0, 5.891117, 7.094252, 8.444403, 10.5};
		double[] d = {0.0, 1.5, 2.8, 3.95, 5.4};
		for (int i = 0; i < d.length; i++) {
			assertEquals(roof[i], JunkLayout.roofY(d[i]), 1e-5, "roof at " + d[i]);
		}
		double[] head = JunkLayout.mastHead();
		assertEquals(22.0, head[1], 1e-9);
		assertEquals(5.769883, head[2], 1e-5);
		double[][] sail = {{0.5, 0.5, 2.716826, 9.282861, 10.526738}, {1.0, 1.0, 7.0, 1.2, 3.0}, {0.3, 0.8, 2.228676, 11.693889, 7.451727}};
		for (double[] r : sail) {
			for (int side = -1; side <= 1; side += 2) {
				double[] p = JunkLayout.sailPoint(side, r[0], r[1]);
				assertEquals(side * r[2], p[0], 1e-5, "sail x at " + r[0] + ", " + r[1]);
				assertEquals(r[3], p[1], 1e-5, "sail y at " + r[0] + ", " + r[1]);
				assertEquals(r[4], p[2], 1e-5, "sail z at " + r[0] + ", " + r[1]);
			}
		}
	}

	@Test
	void dimensions() {
		assertNotNull(GRID);
		assertTrue(G.flying());
		assertFalse(G.submarine());
		assertEquals(TYPE, Ships.byId("dragon_junk"));
		assertEquals(39.0, JunkLayout.BOW_Z - JunkLayout.STERN_Z, 1e-9, "hull length, square bow to transom");
		double overall = JunkLayout.BOWSPRIT[1][2] - JunkLayout.ROOF_BACK_Z;
		assertTrue(overall > 45 && overall < 48, "overall length " + overall);
		assertEquals(8.8, 2 * JunkLayout.HULL_HW, 1e-9, "beam");
		double height = G.topY() - G.lowestY();
		assertTrue(height > 27 && height < 31, "overall height (anchor to masthead) " + height);
		assertTrue(JunkLayout.BEAK_TIP_Z > JunkLayout.BOW_Z + 2.5, "the beak points forwards under the square bow");
		assertTrue(JunkLayout.mastHead()[2] < JunkLayout.MAST_FOOT[2] - 8, "the mast rakes aft");
		assertTrue(G.boundingRadius() >= JunkLayout.BOWSPRIT[1][2]);
		assertTrue(G.aiReach() >= JunkLayout.BOWSPRIT[1][2] && G.aiBack() >= -JunkLayout.ROOF_BACK_Z, "the autopilot's extents");
		assertTrue(G.aiHalfWidth() >= JunkLayout.SAIL_CLEW[0], "the sail's clews are within the autopilot's clearance");
		assertEquals("Jonque du Dragon", TYPE.frenchName());
	}

	/** The terrain probes reach the vessel's extremes: bowsprit, beak, roof, masthead, clews, anchor. */
	@Test
	void probesCoverTheWholeVolume() {
		double minX = 1e9, maxX = -1e9, minY = 1e9, maxY = -1e9, minZ = 1e9, maxZ = -1e9;
		for (double[] p : G.probes()) {
			minX = Math.min(minX, p[0]);
			maxX = Math.max(maxX, p[0]);
			minY = Math.min(minY, p[1]);
			maxY = Math.max(maxY, p[1]);
			minZ = Math.min(minZ, p[2]);
			maxZ = Math.max(maxZ, p[2]);
		}
		assertTrue(maxZ >= JunkLayout.BOWSPRIT[1][2] - 0.1, "bowsprit tip " + maxZ);
		assertTrue(minZ <= JunkLayout.ROOF_BACK_Z + 0.3, "the roof's back " + minZ);
		assertTrue(maxY >= JunkLayout.MAST_HEAD_Y, "the masthead " + maxY);
		assertTrue(minY <= JunkLayout.ANCHOR_BOTTOM_Y + 0.1, "the anchor " + minY);
		assertTrue(maxX >= JunkLayout.SAIL_CLEW[0] - 0.1 && minX <= -JunkLayout.SAIL_CLEW[0] + 0.1, "the clews " + minX + " " + maxX);
		assertTrue(G.probes().size() > 150 && G.probes().size() < 500, "probes " + G.probes().size());
		// the hull's sides are probed all along, on both sides
		for (double z = -18; z <= 20; z += 4) {
			final double zz = z;
			assertTrue(G.probes().stream().anyMatch(p -> Math.abs(p[2] - zz) < 1.1 && p[0] > 0.5), "port side probed at " + z);
			assertTrue(G.probes().stream().anyMatch(p -> Math.abs(p[2] - zz) < 1.1 && p[0] < -0.5), "starboard side probed at " + z);
		}
	}

	@Test
	void seats() {
		ShipGeometry.Seat pilot = G.seats().get(ShipGeometry.PILOT_SEAT);
		assertTrue(pilot.pilot());
		assertTrue(G.seats().size() >= 15, "the pilot and the seats " + G.seats().size());
		double y = pilot.y() - 0.28;
		assertEquals(Q, y, 1e-9, "the pilot stands on the quarterdeck");
		assertEquals(y, floorUnder(pilot.x(), y, pilot.z()), 1e-9, "the pilot's deck");
		assertTrue(fits(pilot.x(), y, pilot.z()), "room for the pilot behind the wheel");
		assertTrue(G.inCarryVolume(pilot.x(), y + 0.5, pilot.z()));
		for (ShipGeometry.Seat s : G.seats()) {
			double[] dm = s.dismountLocal();
			assertTrue(fits(dm[0], dm[1] - 0.02, dm[2]), "dismount of seat " + s.index() + " is free");
			assertEquals(dm[1] - 0.02, floorUnder(dm[0], dm[1] - 0.02, dm[2]), 0.51, "dismount of seat " + s.index() + " is on a floor");
			assertTrue(G.inCarryVolume(s.x(), s.y(), s.z()), "seat " + s.index() + " is carried");
		}
		ShipGeometry.Pick p = G.pick(ORIGIN, 0, Q + 1.6, JunkLayout.PILOT_Z - 1.5, 0, 0, 1, 5);
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
		area("main deck (fore)", -1.5, 1.5, M, 8.6, 10.4);
		area("main deck (waist, starboard)", -2.8, -1.6, M, 3.0, 7.6);
		area("main deck (before the break)", -1.1, 0.1, M, -1.15, 2.6);
		area("main deck (bow)", -1.6, 1.6, M, 17.8, 18.5);
		area("quarterdeck", -1.6, 1.6, Q, -3.8, -2.4);
		area("porch", -1.2, 1.2, Q, -7.6, -6.4);
		area("main room (aisle)", -0.8, 0.8, LO, 5.4, 7.0);
		area("main room (starboard of the table)", -2.6, -2.2, LO, 0.4, 2.4);
		area("main room (foot of the companion)", 2.0, 2.6, LO, -1.0, -0.4);
		area("storage (aisle)", -0.8, 0.8, LO, 8.6, 10.6);
		area("bedroom", -1.0, 0.8, BR, -6.6, -2.4);
		area("stern cabin (by the door)", -1.0, 1.0, Q, -10.6, -9.0);
		area("stern cabin (beside the table)", -2.6, -2.4, Q, -13.6, -12.0);
		area("companion house (landing)", 3.4, 3.4, M, 3.15, 3.15);
		assertFalse(fits(0, LO, 3.5), "the map table is solid");
		assertFalse(fits(0, Q, -12.7), "the stern cabin's table is solid");
		// outside: not carried, nothing to stand on
		assertFalse(G.inCarryVolume(0, -12, 0));
		assertFalse(G.inCarryVolume(15, 3, 0));
		assertEquals(Double.NEGATIVE_INFINITY, floorUnder(8, 3, 0), "beside the junk: open air");
		assertTrue(G.insideHull(0, -2, 0), "the hull is in the grid");
	}

	@Test
	void doorsCloseTheRooms() {
		double[][] doors = { // door, x, y, z (in the doorway)
				{JunkLayout.STERN_DOOR, 0, Q, -8.25}, {JunkLayout.BEDROOM_DOOR, 0, M, -1.75}, {JunkLayout.STORAGE_DOOR, 0, LO, 7.75}};
		for (double[] dd : doors) {
			int k = (int) dd[0];
			assertFalse(fits(dd[1], dd[2], dd[3]), "closed door " + k);
			assertTrue(fits(dd[1], dd[2], dd[3], CLOSED.withDoor(k, true)), "open door " + k);
		}
		assertFalse(fits(2.25, M, 3.75), "companion door closed");
		assertTrue(fits(2.25, M, 3.75, CLOSED.withDoor(JunkLayout.COMPANION_DOOR, true)), "companion door open");
		// the hatch over the storage ladder is walked on when closed
		assertEquals(M, floorUnder(0, M, 11.5), 1e-9);
		assertFalse(fits(0, M - 0.6, 11.5), "hatch closed");
		assertTrue(fits(0, M - 0.6, 11.5, CLOSED.withDoor(JunkLayout.HATCH, true)), "hatch open");
	}

	/** Walks a stair one step at a time (0.5 high, 0.5 deep), checking the floor and the head room. */
	private static double walk(String name, double x, double y, double z0, double dz, int steps, double expected, InteriorGrid.State state) {
		double z = z0;
		for (int i = 0; i < steps * 2 + 2; i++) {
			z += dz / 2;
			double f = floorUnder(x, y + 0.6, z, state);
			assertTrue(Math.abs(f - y) <= 0.5 + 1e-9, name + ": step at z " + z + ": " + f + " from " + y);
			y = f;
			assertTrue(fits(x, y, z, state), name + ": head room at z " + z + " (y " + y + ")");
		}
		assertEquals(expected, y, 1e-9, name + ": arrives");
		return y;
	}

	@Test
	void stairsAndLadder() {
		walk("stair up to the quarterdeck", -2.5, M, 1.5, -0.5, 6, Q, CLOSED);
		walk("companion stair down to the main room", 2.25, M, 3.25, -0.5, 7, LO, CLOSED.withDoor(JunkLayout.COMPANION_DOOR, true));
		for (double y = LO + 0.25; y < M - 0.5; y += 0.5) {
			assertTrue(GRID.ladderAt(0, y, 11.5), "storage ladder at " + y);
		}
	}

	/** No room opens on the outside air: every dry or ladder cell is walled off from the outside across its six faces. */
	@Test
	void noWayOut() {
		int[][] faces = {{1, 0, 0}, {-1, 0, 0}, {0, 1, 0}, {0, -1, 0}, {0, 0, 1}, {0, 0, -1}};
		int leaks = 0;
		String first = null;
		for (int i = 0; i < GRID.nx; i++) {
			for (int j = 0; j < GRID.ny; j++) {
				for (int k = 0; k < GRID.nz; k++) {
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
		assertFalse(fits(0, Q, -19.4), "the transom closes the stern cabin");
		assertFalse(fits(3.9, LO, 3.0), "the bilge closes the main room");
		assertFalse(fits(0, LO, 17.4), "the bow closes the storage");
		assertFalse(fits(0, BR, -9.4), "the bedroom's aft bulkhead");
	}

	/**
	 * Every room is reached from the main deck with the doors open, walking (steps up to half a block, falls) and
	 * climbing the ladder: a flood over the grid's standing places (a 0.6 x 1.8 player in whole cells).
	 */
	@Test
	void roomsConnected() {
		InteriorGrid.State open = CLOSED;
		for (int k = 0; k < 8; k++) {
			open = open.withDoor(k, true);
		}
		InteriorGrid.State st = open;
		Set<Long> seen = new HashSet<>();
		ArrayDeque<int[]> queue = new ArrayDeque<>();
		int[] start = {GRID.ix(-0.25), GRID.iy(M + 0.01), GRID.iz(9.25)};
		assertTrue(stand(start[0], start[1], start[2], st), "standing on the main deck");
		queue.add(start);
		seen.add(key(start));
		while (!queue.isEmpty()) {
			int[] c = queue.poll();
			boolean ladder = GRID.kind(c[0], c[1], c[2]) == InteriorGrid.LADDER || GRID.kind(c[0], c[1] - 1, c[2]) == InteriorGrid.LADDER;
			for (int[] d : new int[][] {{1, 0}, {-1, 0}, {0, 1}, {0, -1}}) {
				for (int dy = 1; dy >= -6; dy--) {
					int[] n = {c[0] + d[0], c[1] + dy, c[2] + d[1]};
					if (!seen.contains(key(n)) && stand(n[0], n[1], n[2], st)) {
						seen.add(key(n));
						queue.add(n);
					}
				}
			}
			if (ladder) {
				for (int dy : new int[] {1, -1}) {
					int[] n = {c[0], c[1] + dy, c[2]};
					if (!seen.contains(key(n)) && free(n[0], n[1], n[2], st)) {
						seen.add(key(n));
						queue.add(n);
					}
				}
			}
		}
		double[][] places = { // name index, x, floor y, z
				{0, 0.0, LO, 6.0}, {1, 0.0, LO, 9.5}, {2, 0.0, BR, -5.0}, {3, 0.0, Q, -10.0}, {4, 0.0, Q, -3.0}, {5, 3.5, M, 3.25},
				{6, -1.0, LO, 13.0}};
		String[] names = {"main room", "storage", "bedroom", "stern cabin", "quarterdeck", "companion house", "storage (fore)"};
		for (double[] p : places) {
			long k = key(new int[] {GRID.ix(p[1]), GRID.iy(p[2] + 0.01), GRID.iz(p[3])});
			assertTrue(seen.contains(k), names[(int) p[0]] + " reached from the main deck");
		}
	}

	private static long key(int[] c) {
		return ((long) c[0] * 4096 + c[1]) * 4096 + c[2];
	}

	private static boolean passable(int i, int j, int k, InteriorGrid.State st) {
		return !InteriorGrid.solid(GRID.kind(i, j, k), st);
	}

	/** A player's 0.6 x 1.8 box (two cells wide here: x and x+1 are both checked half a cell) free at cell (i, j, k). */
	private static boolean free(int i, int j, int k, InteriorGrid.State st) {
		for (int dy = 0; dy < 4; dy++) {
			if (!passable(i, j + dy, k, st)) {
				return false;
			}
		}
		return true;
	}

	private static boolean stand(int i, int j, int k, InteriorGrid.State st) {
		return free(i, j, k, st) && (InteriorGrid.solid(GRID.kind(i, j - 1, k), st) || GRID.kind(i, j - 1, k) == InteriorGrid.LADDER
				|| GRID.kind(i, j, k) == InteriorGrid.LADDER);
	}

	@Test
	void rescueAndFalls() {
		assertEquals(M, G.deckRescueY(0, M - 0.3, 9.5, CLOSED), 1e-9, "sunk into the main deck");
		assertEquals(Q, G.deckRescueY(0, Q - 0.3, -3.0, CLOSED), 1e-9, "sunk into the quarterdeck");
		assertEquals(M, G.deckCrossingY(0, 9.5, 0.4, -1.5, 1e-3, true, CLOSED), 1e-9, "fell through the main deck");
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
		assertTrue(kinds[InteriorGrid.SOLID] > 8000);
		assertTrue(kinds[InteriorGrid.DRY] > 3000);
		assertTrue(kinds[InteriorGrid.LADDER] > 10);
		for (int d = 0; d <= 4; d++) {
			assertTrue(kinds[InteriorGrid.DOOR + d] > 0, "door " + d);
		}
		assertNotNull(G.decor());
		assertTrue(G.decor().seats().size() >= 15, "seats " + G.decor().seats().size());
		assertTrue(G.decor().blocks().size() >= 60, "furniture of the decoration mods " + G.decor().blocks().size());
		for (String mod : new String[] {"farmhouse_decorations:", "furnish:", "farmersdelight:", "landsoficaria:"}) {
			assertTrue(G.decor().blocks().stream().anyMatch(b -> b.block().startsWith(mod)), "uses " + mod);
		}
	}

	// ------------------------------------------------------------------ flight

	@Test
	void handlingIsIntermediate() {
		ShipConfig c = TYPE.defaults().get();
		assertNotNull(c.flight);
		ShipConfig lev = Ships.SKY_LEVIATHAN.defaults().get();
		assertTrue(c.acceleration > lev.acceleration && c.maxTurnRate > lev.maxTurnRate && c.flight.climbSpeed > lev.flight.climbSpeed,
				"livelier than the huge Sky Leviathan");
		// between the slow, majestic Crystal Airship (0.22 b/s2, 5 deg/s) and the agile Rustic Skiff (1.1 b/s2, 20 deg/s)
		assertTrue(c.acceleration > 0.3 && c.acceleration < 1.0, "acceleration " + c.acceleration);
		assertTrue(c.maxTurnRate > 7 && c.maxTurnRate < 16, "turn rate " + c.maxTurnRate);
		assertTrue(c.flight.climbSpeed > 1.0 && c.flight.climbSpeed < 2.4, "climb " + c.flight.climbSpeed);
		assertTrue(c.flight.aiLandingClearance <= 1.0, "it may come down low over the water or the ground");
	}

	@Test
	void flies() {
		ShipConfig cfg = TYPE.defaults().get();
		ShipMover.Obstacles air = (x, y, z) -> y < 40;
		ShipPhysics physics = new ShipPhysics();
		Flight flight = new Flight();
		ShipPose pose = new ShipPose(0, 100, 0, 0);
		for (int i = 0; i < 100; i++) {
			pose = Flight.tick(G, pose, physics, flight, ShipPhysics.Controls.COAST, 0, cfg, air, DT).pose();
		}
		assertEquals(100, pose.y(), 1e-9, "hovers");
		for (int i = 0; i < 200; i++) {
			pose = Flight.tick(G, pose, physics, flight, ShipPhysics.Controls.COAST, cfg.flight.climbSpeed, cfg, air, DT).pose();
		}
		assertEquals(cfg.flight.climbSpeed, flight.vy, 1e-6);
		assertTrue(pose.y() > 105);
		for (int i = 0; i < 40; i++) {
			pose = Flight.tick(G, pose, physics, flight, new ShipPhysics.Controls(cfg.normalSpeed, 0), 0, cfg, air, DT).pose();
		}
		assertTrue(physics.speed > cfg.normalSpeed * 0.15 && physics.speed < cfg.normalSpeed * 0.8, "speed after 2 s " + physics.speed);
		double yaw0 = pose.yaw();
		for (int i = 0; i < 80; i++) {
			pose = Flight.tick(G, pose, physics, flight, new ShipPhysics.Controls(cfg.normalSpeed, 1), 0, cfg, air, DT).pose();
		}
		double turned = Math.abs(ShipPose.wrapDegrees(pose.yaw() - yaw0));
		assertTrue(turned > 8 && turned < 60, "turned " + turned + " degrees in 4 s");
		// it cannot come down into the ground: the anchor stops it
		ShipPose low = new ShipPose(0, 40 - G.lowestY() + 0.3, 0, 0);
		ShipPhysics p2 = new ShipPhysics();
		Flight f2 = new Flight();
		for (int i = 0; i < 100; i++) {
			low = Flight.tick(G, low, p2, f2, ShipPhysics.Controls.COAST, -cfg.flight.descendSpeed, cfg, air, DT).pose();
		}
		assertTrue(low.y() + G.lowestY() >= 39.9, "stopped above the ground: anchor at " + (low.y() + G.lowestY()));
	}
}
