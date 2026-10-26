package fr.medievalships.core;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;

/**
 * The Rustic Skyskiff: shape (same numbers as tools/skiff_shape.py), interior grid (decks, rooms, stairs, ladder,
 * doors, windows, carry volume, no way out through the hull), seats, and nimble flight.
 */
class SkiffTest {
	private static final ShipType TYPE = Ships.RUSTIC_SKIFF;
	private static final ShipGeometry G = TYPE.geometry();
	private static final InteriorGrid GRID = G.interior();
	private static final ShipPose ORIGIN = new ShipPose(0, 0, 0, 0);
	private static final InteriorGrid.State CLOSED = InteriorGrid.State.CLOSED;
	private static final double DT = 0.05;
	private static final double P = SkiffLayout.PILOT_Y;
	private static final double HO = SkiffLayout.HOLD_Y;

	/** Values printed by {@code python3 tools/skiff_shape.py}. */
	@Test
	void matchesModelGenerator() {
		double[][] hull = {
				{-12.5, -2.0, 1.818701, -2.736921, 3.000000},
				{-8.0, -3.0, 1.345893, -3.350000, 3.000000},
				{0.0, -2.5, 2.238245, -3.400000, 1.000000},
				{0.0, 0.5, 3.955774, -3.400000, 1.000000},
				{5.0, -2.0, 1.919403, -2.898133, 1.023929},
				{9.0, 0.5, 1.906060, -1.735156, 1.848315},
				{12.0, 1.5, 1.094155, 0.121875, 2.666164},
				{-5.0, 2.0, 4.095274, -3.442969, 3.000000}};
		for (double[] r : hull) {
			assertEquals(r[2], SkiffLayout.hullX(r[0], r[1]), 1e-5, "hull half width at " + r[0] + ", " + r[1]);
			assertEquals(r[3], SkiffLayout.keelY(r[0]), 1e-5, "keel at " + r[0]);
			assertEquals(r[4], SkiffLayout.sheerY(r[0]), 1e-5, "sheer at " + r[0]);
		}
		double[][] roof = {
				{0.0, 1.0, 5.900000, 7.900000, -8.500000},
				{1.0, 0.5, 2.231945, 9.755626, -5.023952},
				{2.5, 1.0, -5.640527, 8.570663, -4.286401},
				{4.0, 0.8, -4.089211, 8.996967, -13.234575},
				{5.5, 0.95, 5.081568, 8.778849, -13.559128}};
		for (double[] r : roof) {
			double[] p = SkiffLayout.roofPoint(r[0], r[1]);
			for (int i = 0; i < 3; i++) {
				assertEquals(r[2 + i], p[i], 1e-5, "roof at " + r[0] + ", " + r[1]);
			}
		}
		assertEquals(-11.25, SkiffLayout.lowestY(), 1e-9);
		assertEquals(0.5, SkiffLayout.deckY(10.1), 1e-9);
		assertEquals(1.0, SkiffLayout.deckY(11.6), 1e-9);
	}

	@Test
	void dimensions() {
		assertNotNull(GRID);
		assertTrue(G.flying());
		assertFalse(G.submarine());
		assertEquals(TYPE, Ships.byId("rustic_skiff"));
		double hull = SkiffLayout.HULL_BOW_Z - SkiffLayout.HULL_STERN_Z;
		assertTrue(hull > 25 && hull < 28, "hull length " + hull);
		double length = SkiffLayout.BOWSPRIT_TIP_Z - SkiffLayout.TUBE_CENTRE_END_Z;
		assertTrue(length > 37 && length < 42, "overall length (bow beam to the tubes' mouths) " + length);
		assertEquals(8.0, 2 * SkiffLayout.HULL_HW, 1e-9, "beam");
		assertTrue(SkiffLayout.hullHalfWidth(8.0) < 0.6 * SkiffLayout.HULL_HW, "the bow narrows (the step of the top view)");
		assertTrue(SkiffLayout.sheerY(12.5) > SkiffLayout.SHEER_WAIST + 1.5, "raised bow");
		assertTrue(SkiffLayout.PILOT_HW > SkiffLayout.HULL_HW, "the pilot deck overhangs the hull");
		double height = G.topY() - G.lowestY();
		assertTrue(height > 23 && height < 28, "overall height (king post finial to the rear wings' tips) " + height);
		assertTrue(G.boundingRadius() >= -SkiffLayout.TUBE_CENTRE_END_Z);
		assertTrue(G.aiReach() >= SkiffLayout.BOWSPRIT_TIP_Z && G.aiBack() >= -SkiffLayout.TUBE_CENTRE_END_Z - 1e-9);
		assertTrue(G.aiHalfWidth() > 6.2, "the wings' spread");
		assertTrue(G.probes().size() > 150 && G.probes().size() < 400, "probes " + G.probes().size());
		// probes reach the ends of the volume: the bow beam, the tubes, the roof, the wings' tips, the keel spike
		double minY = 0, maxY = 0, minZ = 0, maxZ = 0, maxX = 0;
		for (double[] p : G.probes()) {
			minY = Math.min(minY, p[1]);
			maxY = Math.max(maxY, p[1]);
			minZ = Math.min(minZ, p[2]);
			maxZ = Math.max(maxZ, p[2]);
			maxX = Math.max(maxX, Math.abs(p[0]));
		}
		assertTrue(maxZ >= SkiffLayout.BOWSPRIT_TIP_Z - 1e-9 && minZ <= SkiffLayout.TUBE_CENTRE_END_Z + 1e-9, "probes " + minZ + " .. " + maxZ);
		assertTrue(maxY > SkiffLayout.KING_TOP && minY < -10.9, "probes " + minY + " .. " + maxY);
		assertTrue(maxX > 5.7, "probes reach the wings and the roof's eaves: " + maxX);
	}

	@Test
	void moreNimbleThanTheSteampunkAirship() {
		ShipConfig c = TYPE.defaults().get(), a = Ships.STEAMPUNK_AIRSHIP.defaults().get();
		assertNotNull(c.flight);
		assertTrue(c.acceleration > a.acceleration, "acceleration");
		assertTrue(c.braking > a.braking, "braking");
		assertTrue(c.maxTurnRate > a.maxTurnRate, "turn rate");
		assertTrue(c.turnResponse > a.turnResponse, "turn response");
		assertTrue(c.flight.climbSpeed > a.flight.climbSpeed && c.flight.verticalAcceleration > a.flight.verticalAcceleration, "climb");
		assertTrue(c.acceleration > Ships.SKY_LEVIATHAN.defaults().get().acceleration);
	}

	@Test
	void seats() {
		ShipGeometry.Seat pilot = G.seats().get(ShipGeometry.PILOT_SEAT);
		assertTrue(pilot.pilot());
		assertTrue(G.seats().size() >= 8, "the pilot, the chairs and the benches: " + G.seats().size());
		double y = pilot.y() - 0.28;
		assertEquals(P, y, 1e-9, "the pilot stands on the pilot deck");
		assertEquals(y, floorUnder(pilot.x(), y, pilot.z()), 1e-9, "the pilot's deck");
		assertTrue(fits(pilot.x(), y, pilot.z()), "room for the pilot");
		assertTrue(G.inCarryVolume(pilot.x(), y + 0.5, pilot.z()));
		for (ShipGeometry.Seat s : G.seats()) {
			double[] d = s.dismountLocal();
			assertTrue(fits(d[0], d[1] - 0.02, d[2]), "dismount of seat " + s.index() + " is free");
			assertEquals(d[1] - 0.02, floorUnder(d[0], d[1] - 0.02, d[2]), 0.51, "dismount of seat " + s.index() + " is on a floor");
			assertTrue(G.inCarryVolume(s.x(), s.y(), s.z()), "seat " + s.index() + " is carried");
		}
		// clicking the wheel from behind it
		ShipGeometry.Pick p = G.pick(ORIGIN, 0, P + 1.6, SkiffLayout.PILOT_STAND_Z - 0.8, 0, 0.05, 1, 5);
		assertNotNull(p);
		assertEquals(ShipGeometry.PickKind.HELM, p.kind());
	}

	// ------------------------------------------------------------------ walking

	private static double floorUnder(double x, double y, double z) {
		return floorUnder(x, y, z, CLOSED);
	}

	/** Top of the highest collision box under a local point (within 3 blocks), -infinity if none. */
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
		for (double z = z0; z <= z1 + 1e-9; z += 0.5) {
			for (double x = x0; x <= x1 + 1e-9; x += 0.4) {
				assertEquals(y, floorUnder(x, y, z), 1e-9, name + ": floor at " + x + ", " + z);
				assertTrue(fits(x, y, z), name + ": head room at " + x + ", " + z);
				assertTrue(G.inCarryVolume(x, y + 0.5, z), name + ": carried at " + x + ", " + z);
				assertTrue(G.inCarryVolume(x, y + 1.6, z), name + ": carried (head) at " + x + ", " + z);
			}
		}
	}

	@Test
	void decksAndRooms() {
		area("fore deck", -1.2, 1.2, 0.0, -2.2, 7.0);
		area("fore deck (by the bench)", -1.6, 1.6, 0.0, 3.0, 5.0);
		area("bow corner (under the lean-to)", -0.1, 0.1, 0.5, 10.3, 11.1);
		area("pilot deck (port)", 1.0, 2.6, P, -11.6, -5.6);
		area("pilot deck (starboard)", -2.6, -1.0, P, -11.6, -5.6);
		area("pilot deck (front)", -2.6, 2.6, P, -3.4, -3.3);
		area("pilot deck (behind the wheel)", -0.6, 0.6, P, -6.4, -5.0);
		area("common room (aisle)", -0.8, -0.4, 0.0, -7.1, -3.9);
		area("common room (to the bedroom door)", -1.6, -0.4, 0.0, -7.1, -6.9);
		area("bedroom", -0.8, 0.6, 0.0, -12.0, -8.4);
		area("hold", -0.6, 0.1, HO, -7.1, 2.6);
		area("hold (bow end)", -0.15, 0.15, HO, 2.6, 4.0);
		area("hold (aft end, between the crates)", -0.15, 0.15, HO, -9.9, -7.1);
		assertFalse(fits(-2.2, 0.0, -5.2), "the common room's table is solid");
		assertFalse(fits(0.0, P, SkiffLayout.CANOPY_Z), "the king post is solid");
		assertFalse(fits(0.0, P, -4.25), "the helm is solid");
		// outside: not carried, nothing to stand on
		assertFalse(G.inCarryVolume(0, -14, 0));
		assertFalse(G.inCarryVolume(12, 3, 0));
		assertEquals(Double.NEGATIVE_INFINITY, floorUnder(7, 3, 0), "beside the skiff: open air");
	}

	@Test
	void railsAndWindows() {
		// the balustrade of the pilot deck, chest high all round (no jumping over it in flight), open over the crate stair
		for (double z = -12.5; z <= -3.5; z += 1.0) {
			assertFalse(fits(4.5, P, z), "port balustrade at " + z);
			assertFalse(fits(-4.5, P, z), "starboard balustrade at " + z);
			assertTrue(GRID.solidAt(4.75, P + 1.25, z, CLOSED), "the balustrade is 1.5 high at " + z);
		}
		assertFalse(fits(0.0, P, -13.2), "aft balustrade");
		assertFalse(fits(1.5, P, -2.8), "front balustrade");
		assertTrue(fits(-2.75, P, -2.8), "the gap over the crate stair");
		// the fore deck's bulwark is a block high, a step higher at the bow
		assertFalse(fits(3.6, 0.0, 0.0), "the bulwark");
		// glass in the bedroom's side walls: solid, not open
		assertEquals(InteriorGrid.WINDOW, GRID.kind((int) ((3.25 - GRID.x0) / GRID.cell), (int) ((1.25 - GRID.y0) / GRID.cell),
				(int) ((-10.25 - GRID.z0) / GRID.cell)), "port window");
		assertTrue(GRID.solidAt(3.25, 1.25, -10.25, CLOSED));
		assertTrue(GRID.solidAt(-3.25, 1.25, -10.25, CLOSED));
	}

	@Test
	void doorsCloseTheRooms() {
		double[][] doors = {{SkiffLayout.CABIN_DOOR, 0, 0, SkiffLayout.CABIN_FRONT_Z - 0.25}, {SkiffLayout.BEDROOM_DOOR, -1.0, 0, SkiffLayout.PARTITION_Z}};
		for (double[] d : doors) {
			int k = (int) d[0];
			assertFalse(fits(d[1], d[2], d[3]), "closed door " + k);
			assertTrue(fits(d[1], d[2], d[3], CLOSED.withDoor(k, true)), "open door " + k);
		}
		// the grated hatch of the fore deck is walked on when closed; open, it lets one down the ladder
		assertEquals(0.0, floorUnder(0, 0.0, 2.0), 1e-9);
		assertFalse(fits(0, -0.6, 2.0), "hatch closed");
		assertTrue(fits(0, -0.6, 2.0, CLOSED.withDoor(SkiffLayout.GRATE_HATCH, true)), "hatch open");
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
		walk("crate stair up to the pilot deck", -2.75, 0.0, 0.5, -0.5, 6, P);
		walk("hold stair from the common room", 1.25, 0.0, -3.75, -0.5, 5, HO);
		for (double y = HO + 0.25; y < -0.5; y += 0.5) {
			assertTrue(GRID.ladderAt(0, y, 2.0), "ladder under the grated hatch at " + y);
		}
		assertEquals(HO, floorUnder(0, HO, 2.0), 1e-9, "the ladder's foot on the hold floor");
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
		assertFalse(fits(0, 0, -12.9), "the transom closes the bedroom");
		assertFalse(fits(0, HO, 4.9), "the hold ends at the bow");
		assertFalse(fits(0, HO, -10.9), "the hold ends aft");
		assertFalse(fits(2.4, HO, 0.0), "the bilge closes the hold");
		assertFalse(fits(3.4, 0.0, -6.0), "the cabin's side wall");
	}

	@Test
	void rescueAndFalls() {
		assertEquals(0.0, G.deckRescueY(0, -0.3, 4.0, CLOSED), 1e-9, "sunk into the fore deck");
		assertEquals(P, G.deckRescueY(1.5, P - 0.3, -8.0, CLOSED), 1e-9, "sunk into the pilot deck");
		assertEquals(0.0, G.deckCrossingY(0, 4.0, 0.4, -1.5, 1e-3, true, CLOSED), 1e-9, "fell through the fore deck");
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
		assertTrue(kinds[InteriorGrid.SOLID] > 2000);
		assertTrue(kinds[InteriorGrid.DRY] > 1500);
		assertTrue(kinds[InteriorGrid.LADDER] >= 16);
		assertTrue(kinds[InteriorGrid.WINDOW] >= 8);
		for (int d : new int[] {SkiffLayout.CABIN_DOOR, SkiffLayout.BEDROOM_DOOR, SkiffLayout.GRATE_HATCH}) {
			assertTrue(kinds[InteriorGrid.DOOR + d] > 0, "door " + d);
		}
		assertNotNull(G.decor());
		assertTrue(G.decor().seats().size() >= 7, "seats " + G.decor().seats().size());
		assertTrue(G.decor().blocks().size() >= 50, "furniture of the decoration mods " + G.decor().blocks().size());
		for (String mod : new String[] {"farmhouse_decorations:", "furnish:", "farmersdelight:", "landsoficaria:"}) {
			assertTrue(G.decor().blocks().stream().anyMatch(b -> b.block().startsWith(mod)), "uses " + mod);
		}
		assertTrue(G.decor().blocks().stream().anyMatch(b -> b.block().endsWith("single_bed")), "the bed");
	}

	// ------------------------------------------------------------------ flight

	@Test
	void fliesNimbly() {
		ShipConfig cfg = TYPE.defaults().get();
		ShipMover.Obstacles air = (x, y, z) -> y < 40;
		ShipPhysics physics = new ShipPhysics();
		Flight flight = new Flight();
		ShipPose pose = new ShipPose(0, 100, 0, 0);
		for (int i = 0; i < 100; i++) {
			pose = Flight.tick(G, pose, physics, flight, ShipPhysics.Controls.COAST, 0, cfg, air, DT).pose();
		}
		assertEquals(100, pose.y(), 1e-9, "hovers");
		// full climb: answers quickly
		for (int i = 0; i < 20; i++) {
			pose = Flight.tick(G, pose, physics, flight, ShipPhysics.Controls.COAST, cfg.flight.climbSpeed, cfg, air, DT).pose();
		}
		assertTrue(flight.vy > cfg.flight.climbSpeed * 0.6, "climbing well after one second: " + flight.vy);
		for (int i = 0; i < 60; i++) {
			pose = Flight.tick(G, pose, physics, flight, ShipPhysics.Controls.COAST, cfg.flight.climbSpeed, cfg, air, DT).pose();
		}
		assertEquals(cfg.flight.climbSpeed, flight.vy, 1e-6);
		// forward at normal speed: quick to gather way
		for (int i = 0; i < 40; i++) {
			pose = Flight.tick(G, pose, physics, flight, new ShipPhysics.Controls(cfg.normalSpeed, 0), 0, cfg, air, DT).pose();
		}
		assertTrue(physics.speed > cfg.normalSpeed * 0.3, "speed after 2 s " + physics.speed);
		// a tight turn: hard over for 3 s turns it a long way
		double yaw0 = pose.yaw();
		for (int i = 0; i < 60; i++) {
			pose = Flight.tick(G, pose, physics, flight, new ShipPhysics.Controls(cfg.normalSpeed, 1), 0, cfg, air, DT).pose();
		}
		assertTrue(Math.abs(ShipPose.wrapDegrees(pose.yaw() - yaw0)) > 25, "turned " + ShipPose.wrapDegrees(pose.yaw() - yaw0));
		// it cannot come down into the ground: its lowest point (a wing's tip) stops it
		ShipPose low = new ShipPose(0, 40 - G.lowestY() + 0.3, 0, 0);
		ShipPhysics p2 = new ShipPhysics();
		Flight f2 = new Flight();
		for (int i = 0; i < 100; i++) {
			low = Flight.tick(G, low, p2, f2, ShipPhysics.Controls.COAST, -cfg.flight.descendSpeed, cfg, air, DT).pose();
		}
		assertTrue(low.y() + G.lowestY() >= 39.9, "stopped above the ground: lowest point at " + (low.y() + G.lowestY()));
	}
}
