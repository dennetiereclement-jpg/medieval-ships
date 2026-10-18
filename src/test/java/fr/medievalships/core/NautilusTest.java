package fr.medievalships.core;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;

import fr.medievalships.core.Ships.NautilusLayout;

/** The Nautilus: shape, interior grid (walls, floors, stairs, ladders, hatch, dry spaces) and diving. */
class NautilusTest {
	private static final ShipType NAUTILUS = Ships.NAUTILUS;
	private static final ShipGeometry G = NAUTILUS.geometry();
	private static final InteriorGrid GRID = G.interior();
	private static final ShipPose ORIGIN = new ShipPose(0, 0, 0, 0);
	private static final double DT = 0.05;

	/** Values printed by {@code python3 tools/nautilus_shape.py}. */
	@Test
	void matchesModelGenerator() {
		double[][] rows = {
				{-30.0, 4.936676, 5.465605},
				{-20.0, 6.653710, 7.366607},
				{0.0, 7.000000, 7.750000},
				{20.0, 6.485812, 7.180720},
				{40.0, 1.950459, 2.159437}};
		for (double[] r : rows) {
			assertEquals(r[1], NautilusLayout.halfWidth(r[0]), 1e-5, "half width at " + r[0]);
			assertEquals(r[2], NautilusLayout.halfHeight(r[0]), 1e-5, "half height at " + r[0]);
			assertEquals(r[1], NAUTILUS.hull().halfWidth(r[0]), 1e-5, "hull shape half width at " + r[0]);
		}
	}

	@Test
	void dimensions() {
		assertNotNull(GRID);
		assertTrue(G.submarine());
		assertFalse(Ships.STEAMPUNK_AIRSHIP.geometry().submarine());
		assertEquals(96.0, NautilusLayout.RAM_TIP_Z - NautilusLayout.TAIL_END_Z, 1e-9, "overall length");
		assertEquals(14.0, 2 * NautilusLayout.MAX_HALF_WIDTH, 1e-9, "beam");
		double hull = NautilusLayout.CASING_TOP_Y - (NautilusLayout.AXIS_Y - NautilusLayout.MAX_HALF_HEIGHT);
		assertEquals(17.0, hull, 1e-9, "hull height, casing included");
		double overall = NautilusLayout.LAMP_CAGE_TOP_Y - G.lowestY();
		assertTrue(overall > 22 && overall < 25, "height with the wheelhouse and the keels " + overall);
		assertTrue(G.boundingRadius() >= NautilusLayout.RAM_TIP_Z);
		assertNotNull(NAUTILUS.defaults().get().dive);
		assertTrue(G.seats().get(ShipGeometry.PILOT_SEAT).pilot());
		assertTrue(G.seats().size() >= 13, "the pilot and the chairs of the dining room");
		assertNotNull(G.decor());
		assertTrue(G.decor().blocks().size() > 40);
		// every cell of the grid that is not outside lies inside the hull body, the casing, the wheelhouse, the cage or a keel
		for (int ix = 0; ix < GRID.nx; ix++) {
			for (int iz = 0; iz < GRID.nz; iz++) {
				for (int iy = 0; iy < GRID.ny; iy++) {
					if (GRID.kind(ix, iy, iz) == InteriorGrid.OUT) {
						continue;
					}
					double x = GRID.x0 + (ix + 0.5) * GRID.cell, y = GRID.y0 + (iy + 0.5) * GRID.cell, z = GRID.z0 + (iz + 0.5) * GRID.cell;
					double w = NautilusLayout.halfWidth(z), h = NautilusLayout.halfHeight(z);
					double dy = y - NautilusLayout.AXIS_Y;
					boolean body = w > 0 && (x / w) * (x / w) + (dy / h) * (dy / h) <= 1.0001;
					boolean casing = Math.abs(x) < NautilusLayout.TOWER_HALF_WIDTH && dy > 0 && y < NautilusLayout.LAMP_CAGE_TOP_Y
							&& z > NautilusLayout.CASING_Z0 && z < NautilusLayout.CASING_Z1;
					boolean keel = Math.abs(x) < 0.5 && dy < 0 && y > NautilusLayout.KEEL_BOTTOM_Y - 0.01;
					assertTrue(body || casing || keel, "cell outside the hull at " + x + ", " + y + ", " + z);
				}
			}
		}
	}

	/** Highest floor under a standing player (feet at local y), from the collision boxes. */
	private static double floorUnder(double x, double y, double z, InteriorGrid.State state) {
		double[] top = {Double.NEGATIVE_INFINITY};
		G.collectBoxes(ORIGIN, state, x - 0.3, y - 3, z - 0.3, x + 0.3, y + 0.01, z + 0.3, (a, b, c, d, e, f) -> {
			if (e <= y + 0.01) {
				top[0] = Math.max(top[0], e);
			}
		});
		return top[0];
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

	private static void room(String name, double x0, double x1, double y, double z0, double z1) {
		InteriorGrid.State s = InteriorGrid.State.CLOSED;
		for (double z = z0; z <= z1 + 1e-9; z += 0.7) {
			for (double x = x0; x <= x1 + 1e-9; x += 0.6) {
				assertEquals(y, floorUnder(x, y, z, s), 1e-9, name + ": floor at " + x + ", " + z);
				assertTrue(fits(x, y, z, s), name + ": head room at " + x + ", " + z);
				assertTrue(GRID.dryAt(x, y + 1.0, z, s) && GRID.dryAt(x, y + 1.6, z, s), name + ": dry at " + x + ", " + z);
				assertTrue(G.inCarryVolume(x, y + 0.5, z), name + ": carried at " + x + ", " + z);
			}
		}
	}

	@Test
	void rooms() {
		double m = NautilusLayout.MAIN_FLOOR_Y, l = NautilusLayout.LOWER_FLOOR_Y;
		// the aisles of the furnished rooms
		room("corridor", -1.1, 1.1, m, 20.4, 26.0);
		room("dining room (aisle)", -4.0, 4.0, m, 13.4, 13.9);
		room("dining room (table end)", 3.4, 3.8, m, 13.4, 16.8);
		assertFalse(fits(0, m, 15.5, InteriorGrid.State.CLOSED), "the dining table is solid");
		room("library (aisle)", -0.9, 0.9, m, 7.6, 12.0);
		room("salon (centre)", -0.4, 0.4, m, 2.4, 6.0);
		room("salon (side)", 1.85, 2.15, m, -4.0, 3.6);
		room("salon (corner by the stairs door)", 2.6, 3.1, m, -6.1, -5.0);
		room("nemo", -2.6, -2.4, m, 22.6, 24.0);
		room("aronnax", 2.4, 2.8, m, 22.0, 24.0);
		room("coursive", 2.4, 3.5, l, 5.0, 23.0);
		room("kitchen", -2.8, -2.4, l, 6.5, 13.5);
		room("crew", -2.6, 1.1, l, 15.0, 20.4);
		room("aft corridor", -0.6, 0.6, l, -6.5, 5.0);
		room("wheelhouse", -0.6, 0.6, NautilusLayout.TOWER_FLOOR_Y, 16.0, 18.0);
		room("engine room (batteries)", -3.0, 0.0, l, -20.4, -13.5);
		room("engine room (beside the engine)", 0.4, 1.9, l, -28.0, -22.2);
		room("engine room (passage)", 0.9, 2.1, l, -22.2, -20.4);
		room("catwalk", 2.0, 2.6, m, -25.0, -13.5);
		// the salon is 7 wide, 13 long and 5.5 high
		assertTrue(fits(0, 3.6, 0, InteriorGrid.State.CLOSED), "salon: high ceiling");
		// outside, beside the hull: the sea, not carried, not dry
		InteriorGrid.State s = InteriorGrid.State.CLOSED;
		assertFalse(GRID.dryAt(9.0, 0.5, 0, s));
		assertFalse(G.inCarryVolume(9.0, 0.5, 0));
		assertTrue(GRID.solidAt(6.8, 0.0, 0, s), "pressure hull");
		assertTrue(G.insideHull(0, 0.5, 0));
		assertFalse(G.insideHull(0, 0.5, 53));
		// the great salon windows: an alcove on each side reaching the hull
		assertTrue(GRID.dryAt(5.5, 2.6, 0, s) && GRID.dryAt(-5.5, 2.6, 0, s), "salon bay windows");
		// on the casing, outside: carried (walking on the top of the Nautilus)
		assertTrue(G.inCarryVolume(0, NautilusLayout.CASING_TOP_Y + 0.5, 0));
		assertEquals(NautilusLayout.CASING_TOP_Y, floorUnder(0, NautilusLayout.CASING_TOP_Y, 0, s), 1e-9, "walking on the casing");
	}

	@Test
	void doorsCloseTheRooms() {
		InteriorGrid.State closed = InteriorGrid.State.CLOSED;
		double[][] doors = {{0, 18.25}, {0, 12.75}, {0, 6.75}};
		for (double[] d : doors) {
			assertFalse(fits(d[0], 0, d[1], closed), "closed door at z " + d[1]);
		}
		InteriorGrid.State open = closed.withDoor(3, true).withDoor(4, true).withDoor(5, true);
		for (double[] d : doors) {
			assertTrue(fits(d[0], 0, d[1], open), "open door at z " + d[1]);
		}
	}

	/** Walks up the spiral staircase, clockwise seen from above, one step at a time. */
	@Test
	void spiralStaircase() {
		InteriorGrid.State s = InteriorGrid.State.CLOSED;
		double cx = -1.0, cz = -9.5, r = 1.4;
		double y = NautilusLayout.LOWER_FLOOR_Y;
		// arrive from the aft corridor of the lower level
		assertEquals(y, floorUnder(0, y, -6.6, s), 1e-9, "lower corridor at the foot of the stairs");
		for (double a = 5; a <= 360; a += 5) {
			double x = cx + Math.sin(Math.toRadians(a)) * r, z = cz + Math.cos(Math.toRadians(a)) * r;
			double f = floorUnder(x, y + 0.6, z, s);
			assertTrue(f >= y - 1e-9 && f <= y + 0.5 + 1e-9, "step at " + a + " deg: " + f + " from " + y);
			y = f;
			assertTrue(fits(x, y, z, s), "head room on the stairs at " + a + " deg (y " + y + ")");
		}
		assertEquals(NautilusLayout.MAIN_FLOOR_Y, y, 1e-9, "arrived on the main level");
		// the gallery to the salon door and the landing towards the engine room and the hatch ladder
		assertEquals(0.0, floorUnder(0, 0, -7.25, s), 1e-9);
		assertEquals(0.0, floorUnder(1.5, 0, -11.0, s), 1e-9);
	}

	@Test
	void laddersAndHatches() {
		InteriorGrid.State closed = InteriorGrid.State.CLOSED;
		// up to the hatch on the casing
		for (double y = 0.5; y < 8.4; y += 0.5) {
			assertTrue(GRID.ladderAt(NautilusLayout.HATCH_X, y, NautilusLayout.HATCH_Z), "hatch ladder at " + y);
		}
		double hatchY = NautilusLayout.CASING_TOP_Y - 0.25;
		assertTrue(GRID.solidAt(NautilusLayout.HATCH_X, hatchY, NautilusLayout.HATCH_Z, closed), "hatch closed");
		assertFalse(GRID.solidAt(NautilusLayout.HATCH_X, hatchY, NautilusLayout.HATCH_Z, closed.withDoor(NautilusLayout.HATCH_DOOR, true)),
				"hatch open");
		// up into the wheelhouse through its trap
		for (double y = 0.5; y < 8.5; y += 0.5) {
			assertTrue(GRID.ladderAt(0, y, 19.0), "wheelhouse ladder at " + y);
		}
		assertTrue(GRID.ladderAt(0, NautilusLayout.TOWER_FLOOR_Y + 0.25, 19.0), "the ladder goes on above the trap");
		assertTrue(GRID.solidAt(0, NautilusLayout.TOWER_FLOOR_Y - 0.25, 19.0, closed), "wheelhouse trap closed");
		assertEquals(NautilusLayout.TOWER_FLOOR_Y, floorUnder(0, NautilusLayout.TOWER_FLOOR_Y, 19.0, closed), 1e-9, "walk over the closed trap");
		// the airlock: dry when pumped out, sea when flooded; its outer door in the hull
		assertTrue(GRID.dryAt(0, -3.5, 27.0, closed));
		assertFalse(GRID.dryAt(0, -3.5, 27.0, closed.withAirlock(1f)));
		assertTrue(GRID.kindAt(0, -3.5, 27.0) == InteriorGrid.AIRLOCK);
	}

	@Test
	void rescueAndFalls() {
		InteriorGrid.State s = InteriorGrid.State.CLOSED;
		assertEquals(0.0, G.deckRescueY(0, -0.3, 13.6, s), 1e-9, "sunk into the dining room floor");
		assertTrue(Double.isNaN(G.deckRescueY(0, 0.5, 13.6, s)), "standing in the dining room");
		assertEquals(0.0, G.deckCrossingY(0, 13.6, 0.4, -1.5, 1e-3, true, s), 1e-9, "fell through the main floor");
		assertTrue(Double.isNaN(G.deckCrossingY(0, 13.6, 3.0, 1.0, 1e-3, true, s)), "jumping in the dining room");
	}

	@Test
	void gridFileRoundTrip() {
		int[] kinds = new int[256];
		for (int ix = 0; ix < GRID.nx; ix++) {
			for (int iz = 0; iz < GRID.nz; iz++) {
				for (int iy = 0; iy < GRID.ny; iy++) {
					kinds[GRID.kind(ix, iy, iz) & 0xFF]++;
				}
			}
		}
		assertTrue(kinds[InteriorGrid.SOLID] > 10000);
		assertTrue(kinds[InteriorGrid.DRY] > 20000);
		assertTrue(kinds[InteriorGrid.LADDER] > 100);
		assertTrue(kinds[InteriorGrid.AIRLOCK] > 100);
		for (int d : new int[] {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 15, 16, 17, 18}) {
			assertTrue(kinds[InteriorGrid.DOOR + d] > 0, "door " + d);
		}
	}

	// ------------------------------------------------------------------ diving

	/** Flat sea bed at {@code bed}, open water above. */
	private static ShipMover.Obstacles seaBed(double bed) {
		return (x, y, z) -> y < bed;
	}

	private static ShipPose run(ShipPose pose, Dive dive, ShipPhysics physics, int input, double surfacedY, ShipMover.Obstacles world,
			double seconds) {
		ShipConfig cfg = NAUTILUS.defaults().get();
		for (int i = 0; i < seconds / DT; i++) {
			double vy = Dive.manual(input, pose.y(), surfacedY, cfg.dive);
			pose = Dive.tick(G, pose, physics, dive, ShipPhysics.Controls.COAST, vy, surfacedY, cfg, world, DT).pose();
		}
		return pose;
	}

	@Test
	void divesHoldsAndSurfaces() {
		double surfaced = 62.2;
		ShipMover.Obstacles world = seaBed(10);
		Dive dive = new Dive();
		ShipPhysics physics = new ShipPhysics();
		ShipPose p = new ShipPose(0, surfaced, 0, 0);
		// on the surface it stays there
		p = run(p, dive, physics, 0, surfaced, world, 5);
		assertEquals(surfaced, p.y(), 0.05);
		// it cannot rise above the surfaced position
		p = run(p, dive, physics, 1, surfaced, world, 5);
		assertEquals(surfaced, p.y(), 0.06);
		// dive: slow to start, then about the dive speed
		p = run(p, dive, physics, -1, surfaced, world, 2);
		assertTrue(surfaced - p.y() < 1.0, "heavy: slow to start " + (surfaced - p.y()));
		p = run(p, dive, physics, -1, surfaced, world, 12);
		double depth = surfaced - p.y();
		assertTrue(depth > 9 && depth < 14, "depth " + depth);
		// release: it slows down and holds a depth
		p = run(p, dive, physics, 0, surfaced, world, 8);
		double held = p.y();
		p = run(p, dive, physics, 0, surfaced, world, 10);
		assertEquals(held, p.y(), 0.05, "depth held");
		assertEquals(0, dive.vy, 1e-9);
		// rise back to the surface and stay on it
		p = run(p, dive, physics, 1, surfaced, world, 25);
		assertEquals(surfaced, p.y(), 0.06);
		p = run(p, dive, physics, 0, surfaced, world, 5);
		assertEquals(surfaced, p.y(), 0.06);
	}

	@Test
	void stopsOnTheSeaBed() {
		double surfaced = 62.2;
		double bed = 40.0; // the keels (local -9.5) touch it at y = 49.5
		Dive dive = new Dive();
		ShipPose p = run(new ShipPose(0, surfaced, 0, 0), dive, new ShipPhysics(), -1, surfaced, seaBed(bed), 60);
		assertTrue(p.y() + G.lowestY() >= bed - 0.05, "never into the sea bed: keel at " + (p.y() + G.lowestY()));
		assertTrue(p.y() + G.lowestY() < bed + 1.2, "came down to it: keel at " + (p.y() + G.lowestY()));
		assertEquals(0, dive.vy, 1e-9);
	}

	@Test
	void fallsWithoutWater() {
		Dive dive = new Dive();
		ShipPose p = run(new ShipPose(0, 80, 0, 0), dive, new ShipPhysics(), 0, Double.NaN, seaBed(64), 5);
		assertEquals(64.0, p.y() + G.lowestY(), 0.5, "rests on the ground");
	}

	@Test
	void controlsAreClickable() {
		java.util.List<InteriorDecor.Switch> switches = G.decor().switches();
		java.util.Set<String> actions = new java.util.HashSet<>();
		for (InteriorDecor.Switch w : switches) {
			actions.add(w.action());
		}
		assertEquals(java.util.Set.of("shutters", "floodlight", "lights", "airlock_fill", "airlock_pump", "lifeboat"), actions);
		// the lever of the shutters in the salon, from a player standing in front of it
		double eye = Ships.NautilusLayout.MAIN_FLOOR_Y + 1.62;
		double a = Math.toRadians(40);
		ShipGeometry.Pick pick = G.pick(ORIGIN, 3.0, eye, 1.7, 0, -Math.sin(a), Math.cos(a), 5);
		assertNotNull(pick);
		assertEquals(ShipGeometry.PickKind.SWITCH, pick.kind());
		assertEquals("shutters", switches.get(pick.seat()).action());
		// a valve inside the airlock is not reached through its wall from the corridor
		pick = G.pick(ORIGIN, -0.9, Ships.NautilusLayout.LOWER_FLOOR_Y + 1.6, 23.8, 0, 0, 1, 3);
		assertTrue(pick == null || pick.kind() != ShipGeometry.PickKind.SWITCH || pick.lz() < 24.5, "valve through the wall");
	}

	@Test
	void airlockWaterRises() {
		InteriorGrid.State s = InteriorGrid.State.CLOSED;
		double floor = GRID.airlockFloor, top = GRID.airlockTop;
		assertEquals(Ships.NautilusLayout.LOWER_FLOOR_Y, floor, 1e-6);
		assertTrue(GRID.dryAt(0, floor + 0.3, 27.0, s) && GRID.dryAt(0, top - 0.3, 27.0, s));
		InteriorGrid.State half = s.withAirlock(0.5f);
		assertFalse(GRID.dryAt(0, floor + 0.3, 27.0, half), "under the water");
		assertTrue(GRID.dryAt(0, top - 0.3, 27.0, half), "above the water");
		assertFalse(half.airlockFlooded() || half.airlockDry());
		InteriorGrid.State full = s.withAirlock(1f);
		assertFalse(GRID.dryAt(0, top - 0.3, 27.0, full));
		assertTrue(full.airlockFlooded());
		// the rest of the ship stays dry
		assertTrue(GRID.dryAt(0, 0.5, 13.6, full));
		// every door has a centre
		for (int k : new int[] {0, 8, 9, 16}) {
			assertNotNull(GRID.doorCenter(k), "door " + k);
		}
	}
}
