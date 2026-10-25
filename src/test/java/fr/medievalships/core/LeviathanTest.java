package fr.medievalships.core;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;

/**
 * The Sky Leviathan: shape (same numbers as tools/leviathan_shape.py), interior grid (decks, rooms, stairs,
 * ladders, doors, carry volume), seats, and flight.
 */
class LeviathanTest {
	private static final ShipType TYPE = Ships.SKY_LEVIATHAN;
	private static final ShipGeometry G = TYPE.geometry();
	private static final InteriorGrid GRID = G.interior();
	private static final ShipPose ORIGIN = new ShipPose(0, 0, 0, 0);
	private static final InteriorGrid.State CLOSED = InteriorGrid.State.CLOSED;
	private static final double DT = 0.05;

	/** Values printed by {@code python3 tools/leviathan_shape.py}. */
	@Test
	void matchesModelGenerator() {
		double[][] balloon = {
				{-24.0, 4.964114, 3.987567},
				{-12.0, 11.158131, 8.963089},
				{-0.6, 12.200000, 9.800000},
				{10.0, 11.534071, 9.265073},
				{22.0, 6.353561, 5.103680}};
		for (double[] r : balloon) {
			assertEquals(r[1], LeviathanLayout.balloonHalfWidth(r[0]), 1e-5, "balloon half width at " + r[0]);
			assertEquals(r[2], LeviathanLayout.balloonHalfHeight(r[0]), 1e-5, "balloon half height at " + r[0]);
		}
		double[][] hull = {
				{-18.0, -2.0, 3.757521, -4.638604, 5.500000},
				{-10.0, -4.0, 4.044763, -6.250000, 3.000000},
				{0.0, -5.5, 2.978980, -6.294074, 1.000000},
				{0.0, 0.5, 4.999291, -6.294074, 1.000000},
				{8.0, -3.0, 4.011826, -5.824630, 1.148148},
				{13.0, 2.0, 3.451596, -4.019921, 3.000000},
				{-16.5, 4.5, 3.877010, -5.580115, 5.500000},
				{17.5, 2.5, 1.532011, -1.500000, 3.000000}};
		for (double[] r : hull) {
			assertEquals(r[2], LeviathanLayout.hullX(r[0], r[1]), 1e-5, "hull half width at " + r[0] + ", " + r[1]);
			assertEquals(r[3], LeviathanLayout.keelY(r[0]), 1e-5, "keel at " + r[0]);
			assertEquals(r[4], LeviathanLayout.sheerY(r[0]), 1e-5, "sheer at " + r[0]);
		}
		double[][] fins = {
				{0.000000, 30.564692, -21.364772},
				{5.003285, 26.465944, -34.237120},
				{-5.003285, 26.465944, -34.237120},
				{10.234423, 13.027610, -34.698114},
				{-10.234423, 13.027610, -34.698114},
				{0.000000, 5.477095, -31.735797}};
		for (int k = 0; k < fins.length; k++) {
			double[] p = LeviathanLayout.finPoint(k, LeviathanLayout.FIN_TIP[0], LeviathanLayout.FIN_TIP[1]);
			for (int i = 0; i < 3; i++) {
				assertEquals(fins[k][i], p[i], 1e-5, LeviathanLayout.FIN_NAMES[k] + " tip");
			}
		}
		double[] keel = LeviathanLayout.finPoint(-1, LeviathanLayout.FIN_TIP[0], LeviathanLayout.FIN_TIP[1]);
		assertEquals(-11.553505, keel[1], 1e-5);
		assertEquals(-0.351711, keel[2], 1e-5);
	}

	@Test
	void dimensions() {
		assertNotNull(GRID);
		assertTrue(G.flying());
		assertFalse(G.submarine());
		assertEquals(TYPE, Ships.byId("sky_leviathan"));
		double length = LeviathanLayout.NOSE_SPIKE_Z - LeviathanLayout.tailEndZ();
		assertTrue(length > 64 && length < 69, "overall length " + length);
		assertEquals(52.0, LeviathanLayout.BALLOON_FRONT + LeviathanLayout.BALLOON_REAR, 1e-9, "balloon length");
		assertEquals(24.4, 2 * LeviathanLayout.BALLOON_HW, 1e-9, "balloon width");
		assertEquals(19.6, 2 * LeviathanLayout.BALLOON_HH, 1e-9, "balloon height");
		assertTrue(LeviathanLayout.BALLOON_HW > LeviathanLayout.BALLOON_HH, "the balloon is a little flattened");
		assertEquals(10.0, 2 * LeviathanLayout.HULL_HW, 1e-9, "beam of the ship");
		assertEquals(35.8, LeviathanLayout.HULL_BOW_Z - LeviathanLayout.HULL_STERN_Z, 1e-9, "hull length");
		double height = G.topY() - G.lowestY();
		assertTrue(height > 45 && height < 50, "overall height (flag mast and ventral fin) " + height);
		// the ship hangs under the balloon
		double gap = LeviathanLayout.BALLOON_Y - LeviathanLayout.BALLOON_HH - (LeviathanLayout.POOP_Y + 1.1);
		assertTrue(gap > 1.0, "the stern rail clears the balloon: " + gap);
		assertTrue(G.boundingRadius() >= -LeviathanLayout.tailEndZ());
		assertTrue(G.aiReach() >= LeviathanLayout.NOSE_SPIKE_Z && G.aiBack() >= -LeviathanLayout.tailEndZ() - 1e-9);
		assertNotNull(TYPE.defaults().get().flight);
		assertTrue(TYPE.defaults().get().acceleration < Ships.STEAMPUNK_AIRSHIP.defaults().get().acceleration, "heavier than the small airship");
		assertTrue(G.probes().size() > 200 && G.probes().size() < 600, "probes " + G.probes().size());
	}

	@Test
	void seats() {
		ShipGeometry.Seat pilot = G.seats().get(ShipGeometry.PILOT_SEAT);
		assertTrue(pilot.pilot());
		assertTrue(G.seats().size() >= 9, "the pilot and the benches");
		// the pilot stands on the quarterdeck behind the wheel, free of the helm
		double y = pilot.y() - 0.28;
		assertEquals(LeviathanLayout.QUARTERDECK_Y, y, 1e-9);
		assertEquals(y, floorUnder(pilot.x(), y, pilot.z()), 1e-9, "the pilot's deck");
		assertTrue(fits(pilot.x(), y, pilot.z()), "room for the pilot");
		assertTrue(G.inCarryVolume(pilot.x(), y + 0.5, pilot.z()));
		for (ShipGeometry.Seat s : G.seats()) {
			double[] d = s.dismountLocal();
			assertTrue(fits(d[0], d[1] - 0.02, d[2]), "dismount of seat " + s.index() + " is free");
			assertEquals(d[1] - 0.02, floorUnder(d[0], d[1] - 0.02, d[2]), 0.51, "dismount of seat " + s.index() + " is on a floor");
			assertTrue(G.inCarryVolume(s.x(), s.y(), s.z()), "seat " + s.index() + " is carried");
		}
		// clicking the helm
		ShipGeometry.Pick p = G.pick(ORIGIN, 0, LeviathanLayout.QUARTERDECK_Y + 1.6, LeviathanLayout.PILOT_Z - 1.5, 0, 0, 1, 5);
		assertNotNull(p);
		assertEquals(ShipGeometry.PickKind.HELM, p.kind());
	}

	// ------------------------------------------------------------------ walking

	/** Top of the highest collision box under a local point (within 3 blocks), -infinity if none. */
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

	/** Is a player (0.6 x 1.8) standing at local feet height y free of every collision box? */
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
		double m = LeviathanLayout.MAIN_DECK_Y, c = LeviathanLayout.QUARTERDECK_Y, lo = LeviathanLayout.LOWER_DECK_Y,
				ho = LeviathanLayout.HOLD_Y;
		area("main deck (fore)", -1.4, 0.6, m, 0.4, 8.5);
		area("main deck (aft)", -1.8, 0.6, m, -7.0, -3.4);
		area("main deck (beside the tower)", -2.4, -2.0, m, -3.4, 0.4);
		area("forecastle", -1.0, 1.0, LeviathanLayout.FORECASTLE_Y, 9.9, 12.0);
		area("quarterdeck", -2.0, 2.0, c, -9.8, -8.4);
		area("quarterdeck (aft)", -2.0, -0.9, c, -14.6, -11.6);
		area("poop deck", -1.8, 1.8, LeviathanLayout.POOP_Y, -18.7, -15.9);
		area("observation deck", -3.5, 3.5, LeviathanLayout.TOP_DECK_Y, -10.0, -3.4);
		area("observation deck (fore)", -3.5, 3.5, LeviathanLayout.TOP_DECK_Y, 0.4, 3.4);
		area("captain's office (aisle between the doors)", -0.8, 0.8, m, -12.0, -9.2);
		area("captain's office (by the chart table)", 1.6, 1.8, m, -11.4, -9.6);
		area("captain's bedroom", -1.0, 0.4, m, -18.2, -13.6);
		area("chart room (by the door)", -1.0, 1.0, c, -16.4, -16.0);
		area("chart room (beside the table)", 1.6, 1.8, c, -18.4, -16.2);
		assertFalse(fits(0, c, -17.6), "the chart table is solid");
		area("bosun's store", -0.8, 0.8, m, 10.0, 12.4);
		area("common room (starboard of the table)", -2.4, -2.2, lo, 3.0, 8.6);
		area("common room (port of the table)", 2.2, 2.4, lo, 5.2, 8.6);
		area("common room (aisle)", -0.6, 0.6, lo, 1.6, 4.9);
		area("common room (foot of the companion)", 2.0, 2.4, lo, 1.4, 1.6);
		area("coursive", -0.15, 0.15, lo, -8.6, 0.0);
		area("crew room", -2.1, -1.9, lo, -8.0, -0.5);
		area("storeroom", 2.2, 2.4, lo, -6.5, -1.5);
		area("hold", -1.0, 1.0, ho, -8.5, 6.0);
		area("engine room (landing)", -1.8, 0.6, lo, -10.6, -9.8);
		area("engine room (floor)", -1.9, -1.7, -5.0, -14.6, -12.6);
		area("engine room (in front of the boiler)", -1.6, 0.6, -5.0, -12.65, -12.65);
		area("engine room (catwalk)", -3.0, -3.0, lo + 0.5, -14.9, -11.8);
		assertFalse(fits(0, -5.0, -14.2), "the boiler is solid");
		assertFalse(fits(0, lo, 7.75), "the common room's table is solid");
		// outside: not carried, nothing to stand on
		assertFalse(G.inCarryVolume(0, -14, 0));
		assertFalse(G.inCarryVolume(20, 10, 0));
		assertTrue(G.insideHull(0, 17.8, 0), "the balloon is solid");
		assertTrue(GRID.solidAt(0, 17.8, 10, CLOSED));
		assertEquals(Double.NEGATIVE_INFINITY, floorUnder(8, 3, 0), "beside the ship: open air");
	}

	@Test
	void doorsCloseTheRooms() {
		double[][] doors = { // door, x, y, z (in the doorway)
				{LeviathanLayout.CAPTAIN_DOOR, 0, 0, -7.75}, {3, 0, 0, -12.75}, {4, 0, 3, -15.25}, {5, 0, 0, 9.25}, {6, 0, -3, 0.75},
				{LeviathanLayout.ENGINE_UPPER_DOOR, 0, -3, -9.25}, {LeviathanLayout.TOWER_DOOR, 0, 0, -0.25}};
		for (double[] d : doors) {
			int k = (int) d[0];
			assertFalse(fits(d[1], d[2], d[3]), "closed door " + k);
			assertTrue(fits(d[1], d[2], d[3], CLOSED.withDoor(k, true)), "open door " + k);
		}
		// side doors of the coursive
		assertFalse(fits(-1.25, -3, -4.0), "crew door closed");
		assertTrue(fits(-1.25, -3, -4.0, CLOSED.withDoor(7, true)), "crew door open");
		assertTrue(fits(1.25, -3, -4.0, CLOSED.withDoor(8, true)), "store door open");
		// the trap to the hold is walked on when closed
		assertEquals(-3.0, floorUnder(0, -3.0, -6.0), 1e-9);
		assertFalse(fits(0, -3.6, -6.0), "hatch closed");
		assertTrue(fits(0, -3.6, -6.0, CLOSED.withDoor(LeviathanLayout.HOLD_HATCH, true)), "hatch open");
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

	/** No room opens on the outside air: every dry or ladder cell is walled off from the outside across its six
	 * faces (across the transom, at the stem, under the curve of the bilge), but the companion opening in the
	 * main deck and the tower's ladder shaft, which open on the main deck. */
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
					double x = GRID.x0 + (i + 0.5) * GRID.cell, y = GRID.y0 + (j + 0.5) * GRID.cell, z = GRID.z0 + (k + 0.5) * GRID.cell;
					boolean companion = x > 1.0 && x < 3.5 && y > -1.0 && y < 0.0 && z > 1.0 && z < 5.0;
					boolean shaft = Math.abs(x) < 1.5 && y > 0.0 && z > -3.0 && z < 0.5;
					if (companion || shaft) {
						continue;
					}
					for (int[] f : faces) {
						if (GRID.kind(i + f[0], j + f[1], k + f[2]) == InteriorGrid.OUT) {
							leaks++;
							if (first == null) {
								first = x + ", " + y + ", " + z;
							}
						}
					}
				}
			}
		}
		assertEquals(0, leaks, "room cells open on the outside, first at " + first);
		// the spots where one could walk out before: the transom behind the captain's bedroom and the chart
		// room, the stem in the bosun's store, the bilge of the hold
		assertFalse(fits(0, 0, -19.6), "the transom closes the captain's bedroom");
		assertFalse(fits(0, 3, -19.6), "the transom closes the chart room");
		assertFalse(fits(0, 0, 16.6), "the stem closes the bosun's store");
		assertFalse(fits(2.6, -5.5, 2.5), "the bilge closes the hold");
	}

	@Test
	void stairsAndLadders() {
		walk("quarterdeck stair (port)", 3.25, 0.0, -4.0, -0.5, 7, LeviathanLayout.QUARTERDECK_Y);
		walk("quarterdeck stair (starboard)", -3.25, 0.0, -4.0, -0.5, 7, LeviathanLayout.QUARTERDECK_Y);
		walk("forecastle stair", 2.75, 0.0, 5.5, 0.5, 7, LeviathanLayout.FORECASTLE_Y);
		walk("poop stair", 2.75, 3.0, -12.0, -0.5, 6, LeviathanLayout.POOP_Y);
		walk("companion down to the common room", 2.25, 0.0, 5.0, -0.5, 6, LeviathanLayout.LOWER_DECK_Y);
		walk("engine room stair", 1.75, -3.0, -11.0, -0.5, 5, -5.0);
		// from the engine room's door across the landing (clear of its crates) and up onto the catwalk
		for (double x = 0.0; x >= -3.25 - 1e-9; x -= 0.25) {
			assertEquals(LeviathanLayout.LOWER_DECK_Y, floorUnder(x, LeviathanLayout.LOWER_DECK_Y, -10.0), 1e-9, "landing floor at x " + x);
			assertTrue(fits(x, LeviathanLayout.LOWER_DECK_Y, -10.0), "across the landing at x " + x);
		}
		walk("onto the catwalk", -3.25, LeviathanLayout.LOWER_DECK_Y, -10.0, -0.5, 6, LeviathanLayout.LOWER_DECK_Y + 0.5);
		// the ladder of the tower, from the main deck up through the balloon to the observation deck
		for (double y = 0.25; y < LeviathanLayout.TOP_DECK_Y - 0.5; y += 0.5) {
			assertTrue(GRID.ladderAt(0, y, -1.5), "tower ladder at " + y);
			assertTrue(fits(0, y, -1.5, CLOSED.withDoor(LeviathanLayout.TOP_HATCH, true)) || y > LeviathanLayout.TOP_DECK_Y - 2.0,
					"room in the shaft at " + y);
		}
		assertTrue(GRID.ladderAt(0, LeviathanLayout.TOP_DECK_Y + 0.25, -1.5), "the ladder goes on above the hatch");
		assertTrue(GRID.solidAt(0, LeviathanLayout.TOP_DECK_Y - 0.25, -1.5, CLOSED), "hatch closed");
		assertFalse(GRID.solidAt(0, LeviathanLayout.TOP_DECK_Y - 0.25, -1.5, CLOSED.withDoor(LeviathanLayout.TOP_HATCH, true)), "hatch open");
		assertEquals(LeviathanLayout.TOP_DECK_Y, floorUnder(0, LeviathanLayout.TOP_DECK_Y, -1.5), 1e-9, "walk over the closed hatch");
		// the hold ladder
		for (double y = LeviathanLayout.HOLD_Y + 0.25; y < -3.5; y += 0.5) {
			assertTrue(GRID.ladderAt(0, y, -6.0), "hold ladder at " + y);
		}
	}

	@Test
	void rescueAndFalls() {
		assertEquals(0.0, G.deckRescueY(0, -0.3, 4.0, CLOSED), 1e-9, "sunk into the main deck");
		assertEquals(LeviathanLayout.TOP_DECK_Y, G.deckRescueY(0, LeviathanLayout.TOP_DECK_Y - 0.3, -6.0, CLOSED), 1e-9, "sunk into the top deck");
		assertEquals(0.0, G.deckCrossingY(0, 4.0, 0.4, -1.5, 1e-3, true, CLOSED), 1e-9, "fell through the main deck");
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
		assertTrue(kinds[InteriorGrid.SOLID] > 50000);
		assertTrue(kinds[InteriorGrid.DRY] > 5000);
		assertTrue(kinds[InteriorGrid.LADDER] > 400);
		for (int d : new int[] {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 11}) {
			assertTrue(kinds[InteriorGrid.DOOR + d] > 0, "door " + d);
		}
		assertNotNull(G.decor());
		assertTrue(G.decor().seats().size() >= 20, "seats " + G.decor().seats().size());
		assertTrue(G.decor().blocks().size() >= 150, "furniture of the decoration mods " + G.decor().blocks().size());
		for (String mod : new String[] {"farmhouse_decorations:", "furnish:", "farmersdelight:", "landsoficaria:", "mebahelcreaturesdwarven:"}) {
			assertTrue(G.decor().blocks().stream().anyMatch(b -> b.block().startsWith(mod)), "uses " + mod);
		}
	}

	// ------------------------------------------------------------------ flight

	@Test
	void fliesHeavily() {
		ShipConfig cfg = TYPE.defaults().get();
		ShipMover.Obstacles air = (x, y, z) -> y < 40;
		ShipPhysics physics = new ShipPhysics();
		Flight flight = new Flight();
		ShipPose pose = new ShipPose(0, 100, 0, 0);
		for (int i = 0; i < 200; i++) {
			pose = Flight.tick(G, pose, physics, flight, ShipPhysics.Controls.COAST, 0, cfg, air, DT).pose();
		}
		assertEquals(100, pose.y(), 1e-9, "hovers");
		// full climb: slow to answer (heavy), then steady
		for (int i = 0; i < 20; i++) {
			pose = Flight.tick(G, pose, physics, flight, ShipPhysics.Controls.COAST, cfg.flight.climbSpeed, cfg, air, DT).pose();
		}
		assertTrue(flight.vy < cfg.flight.climbSpeed * 0.6, "still gathering vertical speed after one second: " + flight.vy);
		for (int i = 0; i < 200; i++) {
			pose = Flight.tick(G, pose, physics, flight, ShipPhysics.Controls.COAST, cfg.flight.climbSpeed, cfg, air, DT).pose();
		}
		assertEquals(cfg.flight.climbSpeed, flight.vy, 1e-6);
		assertTrue(pose.y() > 110);
		// forward at normal speed: takes a long time to gather way
		for (int i = 0; i < 40; i++) {
			pose = Flight.tick(G, pose, physics, flight, new ShipPhysics.Controls(cfg.normalSpeed, 0), 0, cfg, air, DT).pose();
		}
		assertTrue(physics.speed > 0.2 && physics.speed < cfg.normalSpeed * 0.6, "speed after 2 s " + physics.speed);
		// it cannot come down into the ground: the ventral fin stops it
		ShipPose low = new ShipPose(0, 40 - G.lowestY() + 0.3, 0, 0);
		ShipPhysics p2 = new ShipPhysics();
		Flight f2 = new Flight();
		for (int i = 0; i < 100; i++) {
			low = Flight.tick(G, low, p2, f2, ShipPhysics.Controls.COAST, -cfg.flight.descendSpeed, cfg, air, DT).pose();
		}
		assertTrue(low.y() + G.lowestY() >= 39.9, "stopped above the ground: keel at " + (low.y() + G.lowestY()));
	}
}
