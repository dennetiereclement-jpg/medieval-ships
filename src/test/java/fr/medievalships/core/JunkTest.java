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
		double[][] keel = {{-19.3, 1.7}, {-18.6, 0.031947}, {-14.0, -4.15}, {-6.0, -5.094733}, {15.0, -4.205185}, {21.0, -3.723757}};
		for (double[] r : keel) {
			assertEquals(r[1], JunkLayout.keelY(r[0]), 1e-5, "keel at " + r[0]);
		}
		double[][] sheer = {{3.0, 1.0}, {0.5, 1.250191}, {-0.4, 1.955952}, {-1.2, 2.44856}, {-5.0, 2.5}, {14.0, 1.177466}, {19.0, 1.740997}};
		for (double[] r : sheer) {
			assertEquals(r[1], JunkLayout.sheerY(r[0]), 1e-5, "sheer at " + r[0]);
		}
		double[][] transom = {{0.5, -19.1}, {1.5, -19.25}, {2.4, -19.475}};
		for (double[] r : transom) {
			assertEquals(r[1], JunkLayout.transomZ(r[0]), 1e-5, "transom at " + r[0]);
		}
		double[][] hull = {{0.0, -3.5, 2.554174}, {0.0, -2.0, 4.004976}, {-16.0, -1.0, 3.118936}, {15.0, -3.0, 1.413054}, {18.5, -2.5, 0.690274},
				{20.5, -2.8, 0.217629}, {19.0, 0.5, 2.489307}, {-18.0, 1.5, 3.998098}, {-12.0, -4.0, 0.840632}, {-18.8, 0.5, 0.882938},
				{-19.3, 2.0, 3.913698}, {18.0, -1.2, 1.866352}};
		for (double[] r : hull) {
			assertEquals(r[2], JunkLayout.hullX(r[0], r[1]), 1e-5, "hull half width at " + r[0] + ", " + r[1]);
		}
		double[] roof = {6.15, 7.981692, 9.438888, 10.537245, 11.5};
		double[] d = {0.0, 1.25, 2.45, 3.6, 5.2};
		for (int i = 0; i < d.length; i++) {
			assertEquals(roof[i], JunkLayout.roofY(d[i]), 1e-5, "roof at " + d[i]);
		}
		assertEquals(7.640348, JunkLayout.roofTop(1.0), 1e-5);
		assertEquals(10.602269, JunkLayout.roofTop(3.0), 1e-5);
		assertEquals(12.323828, JunkLayout.roofTop(5.0), 1e-5);
		// either side of each tier's lower edge (ROOF_EDGES), as tools/junk_shape.py prints them
		double[][] top = {{1.35, 8.114656}, {1.5, 8.610242}, {2.2, 9.460624}, {2.3, 9.873565}, {3.3, 10.880425}, {3.4, 11.268436}};
		for (double[] r : top) {
			assertEquals(r[1], JunkLayout.roofTop(r[0]), 1e-5, "roof top at " + r[0]);
		}
		assertEquals(-5.45, JunkLayout.roofFrontZ(0.0), 1e-9);
		assertEquals(-4.79, JunkLayout.roofFrontZ(2.0), 1e-9);
		assertEquals(-3.734, JunkLayout.roofFrontZ(5.2), 1e-9);
		double[][] rise = {{5.2, -8.0, 0.285208}, {5.2, -12.0, 0.552632}, {2.6, -18.3, 0.282843}, {5.2, -15.7, 0.8}};
		for (double[] r : rise) {
			assertEquals(r[2], JunkLayout.roofRise(r[0], r[1]), 1e-5, "roof rise at " + r[0] + ", " + r[1]);
		}
		assertEquals(-2.206452, JunkLayout.beakTop(21.0), 1e-5);
		double[] head = JunkLayout.mastHead();
		assertEquals(22.0, head[1], 1e-9);
		assertEquals(5.769883, head[2], 1e-5);
		double[][] sail = {{0.5, 0.5, 2.579854, 10.246145, 9.877791}, {1.0, 1.0, 6.4, 1.2, 3.0}, {0.3, 0.8, 2.091713, 13.074056, 6.724894}};
		for (double[] r : sail) {
			for (int side = -1; side <= 1; side += 2) {
				double[] p = JunkLayout.sailPoint(side, r[0], r[1]);
				assertEquals(side * r[2], p[0], 1e-5, "sail x at " + r[0] + ", " + r[1]);
				assertEquals(r[3], p[1], 1e-5, "sail y at " + r[0] + ", " + r[1]);
				assertEquals(r[4], p[2], 1e-5, "sail z at " + r[0] + ", " + r[1]);
			}
		}
	}

	/** The hull's shape: a square bow about half the beam, the beam aft of amidships, a rocker, a raised bow, the counter. */
	@Test
	void hullShape() {
		assertTrue(JunkLayout.BOW_HW < 0.6 * JunkLayout.HULL_HW, "the bow face is about half the beam");
		assertTrue(JunkLayout.planHw(14.0) < JunkLayout.HULL_HW - 0.8, "the forward third narrows steadily");
		assertTrue(JunkLayout.keelY(14.0) > JunkLayout.keelY(0.0) + 0.6, "the keel rises forwards (rocker)");
		assertTrue(JunkLayout.sheerY(JunkLayout.BOW_Z) > JunkLayout.SHEER_FORE + 0.6, "the bow is raised");
		assertTrue(JunkLayout.TRANSOM_FOOT[1] > JunkLayout.MAIN_DECK_Y, "the counter sweeps up to a high transom");
		assertTrue(JunkLayout.transomZ(JunkLayout.QUARTERDECK_Y) < JunkLayout.transomZ(JunkLayout.TRANSOM_FOOT[1]), "the transom rakes aft");
		assertTrue(JunkLayout.hullX(-14.0, -3.0) < 0.6 * JunkLayout.hullX(-14.0, 0.0), "a V-shaped run under the counter");
	}

	@Test
	void dimensions() {
		assertNotNull(GRID);
		assertTrue(G.flying());
		assertFalse(G.submarine());
		assertEquals(TYPE, Ships.byId("dragon_junk"));
		assertEquals(39.0, JunkLayout.BOW_Z - JunkLayout.STERN_Z, 1e-9, "hull length, square bow to transom");
		double overall = JunkLayout.BOWSPRIT[1][2] - JunkLayout.ROOF_BACK_Z;
		assertTrue(overall > 43 && overall < 47, "overall length " + overall);
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

	/**
	 * Every vertex of the stern's outside parts (as the mod reads the model: src/test/resources/dragon_junk_reference_quads.json,
	 * written by tools/reference_quads.py) lies within 2.5 blocks of a terrain probe: the stern gallery, the roof's tiles,
	 * eaves, eave beams and corner posts, the hipped back over the gallery, the gable over the porch. Left out: the hull
	 * (probed by sections), the inside of the stern house and of its roof, what stands over the ridge (the spire and the
	 * staff have their own probes).
	 */
	@Test
	void sternWithinReachOfProbes() throws Exception {
		com.google.gson.JsonObject ref;
		try (java.io.Reader r = new java.io.InputStreamReader(JunkTest.class.getResourceAsStream("/dragon_junk_reference_quads.json"),
				java.nio.charset.StandardCharsets.UTF_8)) {
			ref = com.google.gson.JsonParser.parseReader(r).getAsJsonObject();
		}
		double ytop = JunkLayout.ridgeTop() + JunkLayout.RIDGE_RISE + 0.6, zmax = JunkLayout.roofFrontZ(JunkLayout.ROOF_HW) + 0.6;
		double worst = 0;
		double[] at = null;
		int n = 0;
		for (com.google.gson.JsonElement q : ref.getAsJsonArray("quads")) {
			com.google.gson.JsonArray c = q.getAsJsonArray().get(0).getAsJsonArray();
			for (int i = 0; i < 12; i += 3) {
				double x = c.get(i).getAsDouble(), y = c.get(i + 1).getAsDouble(), z = c.get(i + 2).getAsDouble();
				if (z > zmax || y > ytop || y < JunkLayout.QUARTERDECK_Y) {
					continue;
				}
				double sh = JunkLayout.sheerY(z);
				if (z >= JunkLayout.STERN_Z && Math.abs(x) <= JunkLayout.hullX(z, Math.min(y, sh)) + 0.2 && y <= sh + JunkLayout.RAIL_H) {
					continue;                     // the hull
				}
				double d = Math.min(JunkLayout.ROOF_HW - Math.abs(x), z - JunkLayout.ROOF_BACK_Z);
				if (Math.abs(x) < JunkLayout.ROOF_HW - 0.4 && z > JunkLayout.ROOF_BACK_Z + 0.4 && z < JunkLayout.roofFrontZ(d) - 0.4
						&& y < JunkLayout.roofTop(d) + JunkLayout.roofRise(d, z) - 0.7) {
					continue;                     // inside the stern house and its roof
				}
				n++;
				double best = 1e9;
				for (double[] p : G.probes()) {
					best = Math.min(best, Math.hypot(Math.hypot(p[0] - x, p[1] - y), p[2] - z));
				}
				if (best > worst) {
					worst = best;
					at = new double[] {x, y, z};
				}
			}
		}
		assertTrue(n > 5000, "stern vertices checked " + n);
		assertTrue(worst <= 2.5, "farthest from a probe: " + worst + " at " + java.util.Arrays.toString(at));
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
		area("main deck (waist, starboard)", -2.5, -1.6, M, 3.8, 7.3);
		area("main deck (before the break)", -1.1, 0.1, M, -1.15, 2.6);
		area("main deck (bow)", -1.2, 1.2, M, 17.85, 18.5);
		area("quarterdeck", -1.6, 1.6, Q, -3.8, -2.4);
		area("porch", -1.2, 1.2, Q, -7.6, -6.4);
		area("main room (aisle)", -0.8, 0.8, LO, 5.4, 7.0);
		area("main room (starboard of the table)", -2.6, -2.2, LO, 0.4, 2.4);
		area("main room (foot of the companion)", 2.0, 2.6, LO, -1.0, -0.4);
		area("storage (starboard of the pillar)", -1.3, -0.85, LO, 9.4, 10.6);
		area("storage (port of the pillar)", 0.85, 1.25, LO, 9.5, 9.7);
		area("bedroom", -1.0, 0.6, BR, -6.6, -3.5);
		area("stern cabin (by the door)", -1.0, 1.0, Q, -10.6, -9.0);
		area("stern cabin (beside the table)", -2.6, -2.4, Q, -13.6, -12.0);
		area("companion house (landing)", 3.4, 3.4, M, 3.15, 3.15);
		assertFalse(fits(0, LO, 3.5), "the map table is solid");
		assertFalse(fits(0, LO, 9.5), "the storage's pillar is solid");
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
					boolean outsideLadder = GRID.z0 + (k + 0.5) * GRID.cell > JunkLayout.BOW_Z;   // the rope ladder down the bow face
					if (kind != InteriorGrid.DRY && (kind != InteriorGrid.LADDER || outsideLadder)) {
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
				{0, 0.0, LO, 6.0}, {1, -1.0, LO, 9.5}, {2, 0.0, BR, -5.0}, {3, 0.0, Q, -10.0}, {4, 0.0, Q, -3.0}, {5, 3.5, M, 3.25},
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

	/**
	 * No trap outside: from every place a player can reach from the main deck (jumping a block, falling, climbing ladders,
	 * a 2 x 2 cells footprint standing on whichever cell holds it), the main deck can be reached again; whoever drops onto
	 * the beak climbs the rope ladder down the bow face back aboard.
	 */
	@Test
	void noTrapOutside() {
		InteriorGrid.State open = CLOSED;
		for (int k = 0; k < 8; k++) {
			open = open.withDoor(k, true);
		}
		InteriorGrid.State st = open;
		int[] start = {GRID.ix(-0.5), GRID.iy(M + 0.01), GRID.iz(9.0)};
		assertTrue(stand2(start[0], start[1], start[2], st), "standing on the main deck");
		java.util.Map<Long, java.util.List<Long>> back = new java.util.HashMap<>();
		Set<Long> seen = new HashSet<>();
		ArrayDeque<int[]> queue = new ArrayDeque<>();
		queue.add(start);
		seen.add(key(start));
		boolean beak = false;
		while (!queue.isEmpty()) {
			int[] c = queue.poll();
			for (int[] n : moves(c, st)) {
				back.computeIfAbsent(key(n), q -> new java.util.ArrayList<>()).add(key(c));
				if (seen.add(key(n))) {
					queue.add(n);
					beak |= GRID.z0 + (n[2] + 1) * GRID.cell > JunkLayout.BOW_Z + 0.4;
				}
			}
		}
		Set<Long> home = new HashSet<>();
		ArrayDeque<Long> q2 = new ArrayDeque<>();
		home.add(key(start));
		q2.add(key(start));
		while (!q2.isEmpty()) {
			for (long p : back.getOrDefault(q2.poll(), java.util.List.of())) {
				if (home.add(p)) {
					q2.add(p);
				}
			}
		}
		assertTrue(beak, "the beak is reached (jumping on the bulwark and dropping off the bow)");
		seen.removeAll(home);
		assertEquals(0, seen.size(), "places from which the main deck cannot be reached again");
	}

	private static boolean free2(int i, int j, int k, InteriorGrid.State st) {
		for (int a = 0; a < 2; a++) {
			for (int c = 0; c < 2; c++) {
				for (int dy = 0; dy < 4; dy++) {
					if (!passable(i + a, j + dy, k + c, st)) {
						return false;
					}
				}
			}
		}
		return true;
	}

	private static boolean ladder2(int i, int j0, int j1, int k) {
		for (int a = 0; a < 2; a++) {
			for (int c = 0; c < 2; c++) {
				for (int j = j0; j <= j1; j++) {
					if (GRID.kind(i + a, j, k + c) == InteriorGrid.LADDER) {
						return true;
					}
				}
			}
		}
		return false;
	}

	private static boolean stand2(int i, int j, int k, InteriorGrid.State st) {
		if (!free2(i, j, k, st)) {
			return false;
		}
		for (int a = 0; a < 2; a++) {
			for (int c = 0; c < 2; c++) {
				if (!passable(i + a, j - 1, k + c, st)) {
					return true;
				}
			}
		}
		return ladder2(i, j - 1, j, k);
	}

	private static java.util.List<int[]> moves(int[] c, InteriorGrid.State st) {
		java.util.List<int[]> out = new java.util.ArrayList<>();
		for (int[] d : new int[][] {{1, 0}, {-1, 0}, {0, 1}, {0, -1}}) {
			for (int dy = 2; dy >= -12; dy--) {
				boolean clear = true;
				for (int q = 1; q <= dy; q++) {
					clear &= free2(c[0], c[1] + q, c[2], st);     // jumping: room above
				}
				if (!clear) {
					continue;
				}
				int[] n = {c[0] + d[0], c[1] + dy, c[2] + d[1]};
				if (dy < 0 && !free2(n[0], c[1], n[2], st)) {
					break;                                      // falling: the step sideways must be clear first
				}
				if (stand2(n[0], n[1], n[2], st)) {
					out.add(n);
					break;
				}
				if (dy <= 0 && !free2(n[0], n[1], n[2], st)) {
					break;                                      // landed on something it cannot stand on: no going through
				}
			}
		}
		if (ladder2(c[0], c[1] - 1, c[1] + 1, c[2])) {
			for (int dy : new int[] {1, -1}) {
				int[] n = {c[0], c[1] + dy, c[2]};
				if (free2(n[0], n[1], n[2], st) && (ladder2(n[0], n[1] - 1, n[1], n[2]) || stand2(n[0], n[1], n[2], st))) {
					out.add(n);
				}
			}
		}
		return out;
	}

	/** Skimming the water: holds within the hover height, rises below it, leaves it alone above it or when climbing. */
	@Test
	void skimsTheWater() {
		double a = 0.045;
		double h = JunkLayout.WATER_HOVER;
		assertEquals(a, JunkLayout.skimVy(h - 0.1, -1.2, a), 1e-12, "within the hover band a descent is cancelled");
		assertEquals(0.6, JunkLayout.skimVy(h - 0.6, -1.2, a), 1e-12, "pushed below it, it rises");
		assertEquals(-1.2, JunkLayout.skimVy(h + 0.3, -1.2, a), 1e-12, "higher up, nothing changes");
		assertEquals(-1.2, JunkLayout.skimVy(Double.NaN, -1.2, a), 1e-12, "no water, nothing changes");
		assertEquals(1.3, JunkLayout.skimVy(h - 0.1, 1.3, a), 1e-12, "climbing is never held back");
		assertEquals(1.3, JunkLayout.skimVy(h - 0.6, 1.3, a), 1e-12, "climbing faster than the rise is kept");
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
