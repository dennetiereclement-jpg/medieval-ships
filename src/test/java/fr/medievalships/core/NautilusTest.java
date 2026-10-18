package fr.medievalships.core;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.ArrayList;
import java.util.List;

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
				{-40.0, 2.671694, 3.244200},
				{-20.0, 6.163328, 7.484041},
				{0.0, 7.000000, 8.500000},
				{20.0, 6.143529, 7.460000},
				{40.0, 1.777015, 2.157804}};
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
		assertEquals(17.0, 2 * NautilusLayout.MAX_HALF_HEIGHT, 1e-9, "hull height");
		assertEquals(-8.0, G.lowestY(), 1e-9);
		assertTrue(G.boundingRadius() >= NautilusLayout.RAM_TIP_Z);
		assertNotNull(NAUTILUS.defaults().get().dive);
		assertTrue(G.seats().get(ShipGeometry.PILOT_SEAT).pilot());
		// every cell of the grid that is not outside lies inside the hull body or the wheelhouse
		for (int ix = 0; ix < GRID.nx; ix++) {
			for (int iz = 0; iz < GRID.nz; iz++) {
				for (int iy = 0; iy < GRID.ny; iy++) {
					if (GRID.kind(ix, iy, iz) == InteriorGrid.OUT) {
						continue;
					}
					double x = GRID.x0 + (ix + 0.5) * GRID.cell, y = GRID.y0 + (iy + 0.5) * GRID.cell, z = GRID.z0 + (iz + 0.5) * GRID.cell;
					double w = NautilusLayout.halfWidth(z), h = NautilusLayout.halfHeight(z);
					boolean body = w > 0 && (x / w) * (x / w) + ((y - NautilusLayout.AXIS_Y) / h) * ((y - NautilusLayout.AXIS_Y) / h) <= 1.0001;
					boolean tower = z > NautilusLayout.TOWER_Z0 - 0.01 && z < NautilusLayout.TOWER_Z1 + 0.01 && Math.abs(x) < 2.01
							&& y < NautilusLayout.TOWER_TOP_Y + 0.01;
					assertTrue(body || tower, "cell outside the hull at " + x + ", " + y + ", " + z);
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

	@Test
	void walkTheMainLevel() {
		InteriorGrid.State s = InteriorGrid.State.CLOSED;
		for (double z = -24; z <= 26; z += 0.7) {
			for (double x = -2.4; x <= 2.4; x += 0.6) {
				if (x < -0.7 && z > 9.7 && z < 14.8) {
					continue; // the stairwell
				}
				if (Math.abs(x) < 0.85 && (Math.abs(z - 19.25) < 0.6 || Math.abs(z - 26.75) < 0.6)) {
					continue; // the pillars of the ladders
				}
				assertEquals(NautilusLayout.MAIN_FLOOR_Y, floorUnder(x, 0, z, s), 1e-9, "floor at " + x + ", " + z);
				assertTrue(fits(x, 0, z, s), "head room at " + x + ", " + z);
				assertTrue(GRID.dryAt(x, 1.0, z, s) && GRID.dryAt(x, 1.6, z, s), "dry at " + x + ", " + z);
				assertTrue(G.inCarryVolume(x, 0.5, z));
			}
			// walls of the hall on both sides
			assertFalse(fits(3.3, 0, z, s), "port wall at " + z);
			assertFalse(fits(-3.3, 0, z, s), "starboard wall at " + z);
		}
		// outside, beside the hull: the sea, not carried, not dry
		assertFalse(GRID.dryAt(9.0, 0.5, 0, s));
		assertFalse(G.inCarryVolume(9.0, 0.5, 0));
		assertTrue(GRID.solidAt(6.8, 0.5, 0, s), "pressure hull");
		assertTrue(G.insideHull(0, 0.5, 0));
		assertFalse(G.insideHull(0, 0.5, 47.9 + 5));
	}

	@Test
	void stairsBetweenTheLevels() {
		InteriorGrid.State s = InteriorGrid.State.CLOSED;
		double x = -1.75;
		double y = NautilusLayout.LOWER_FLOOR_Y;
		assertEquals(y, floorUnder(0, y, 0, s), 1e-9, "lower level floor");
		assertTrue(fits(0, y, 0, s), "head room on the lower level");
		// climb the steps: every step at most 0.5 above the previous one, head room all the way
		for (double z = 9.6; z <= 15.0; z += 0.1) {
			double f = floorUnder(x, y + 0.6, z, s);
			assertTrue(f >= y - 1e-9 && f <= y + 0.5 + 1e-9, "step at z=" + z + ": " + f + " from " + y);
			y = f;
			assertTrue(fits(x, y, z, s), "head room on the stairs at z=" + z);
		}
		assertEquals(NautilusLayout.MAIN_FLOOR_Y, y, 1e-9, "arrived on the main level");
	}

	@Test
	void ladderAndHatch() {
		InteriorGrid.State closed = InteriorGrid.State.CLOSED;
		InteriorGrid.State open = closed.withDoor(NautilusLayout.HATCH_DOOR, true);
		double z = NautilusLayout.HATCH_Z;
		for (double y = 0.5; y < 7.0; y += 0.5) {
			assertTrue(GRID.ladderAt(0, y, z), "ladder at " + y);
		}
		// the hatch at the top of the shaft closes the hull
		double top = NautilusLayout.AXIS_Y + NautilusLayout.halfHeight(z) * Math.sqrt(1 - 0.25 / Math.pow(NautilusLayout.halfWidth(z), 2));
		assertTrue(GRID.solidAt(0, top - 0.3, z, closed), "hatch closed");
		assertFalse(GRID.solidAt(0, top - 0.3, z, open), "hatch open");
		assertTrue(G.inCarryVolume(0, top + 1.0, z - 3), "on the top of the hull");
		// ladder from the main level up into the wheelhouse, and room to stand at the helm
		assertTrue(GRID.ladderAt(0, 5.0, 26.0));
		assertEquals(NautilusLayout.TOWER_FLOOR_Y, floorUnder(0, NautilusLayout.TOWER_FLOOR_Y, NautilusLayout.PILOT_Z - 1.5, closed), 1e-9);
		assertTrue(fits(0, NautilusLayout.TOWER_FLOOR_Y, NautilusLayout.PILOT_Z - 1.5, closed));
	}

	@Test
	void rescueAndFalls() {
		InteriorGrid.State s = InteriorGrid.State.CLOSED;
		assertEquals(0.0, G.deckRescueY(0, -0.3, 0, s), 1e-9, "sunk into the main floor");
		assertTrue(Double.isNaN(G.deckRescueY(0, 0.5, 0, s)), "standing in the hall");
		assertEquals(0.0, G.deckCrossingY(0, 0, 0.4, -1.5, 1e-3, true, s), 1e-9, "fell through the main floor");
		assertTrue(Double.isNaN(G.deckCrossingY(0, 0, 3.0, 1.0, 1e-3, true, s)), "jumping in the hall");
	}

	@Test
	void gridFileRoundTrip() {
		List<Integer> kinds = new ArrayList<>();
		for (int k = 0; k < 256; k++) {
			kinds.add(0);
		}
		for (int ix = 0; ix < GRID.nx; ix++) {
			for (int iz = 0; iz < GRID.nz; iz++) {
				for (int iy = 0; iy < GRID.ny; iy++) {
					int k = GRID.kind(ix, iy, iz) & 0xFF;
					kinds.set(k, kinds.get(k) + 1);
				}
			}
		}
		assertTrue(kinds.get(InteriorGrid.SOLID) > 10000);
		assertTrue(kinds.get(InteriorGrid.DRY) > 5000);
		assertTrue(kinds.get(InteriorGrid.LADDER) > 20);
		assertTrue(kinds.get(InteriorGrid.DOOR + NautilusLayout.HATCH_DOOR) > 0);
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
		double bed = 40.0; // the keel (local -8) touches it at y = 48
		Dive dive = new Dive();
		ShipPose p = run(new ShipPose(0, surfaced, 0, 0), dive, new ShipPhysics(), -1, surfaced, seaBed(bed), 60);
		assertTrue(p.y() + G.lowestY() >= bed - 0.01, "never into the sea bed: keel at " + (p.y() + G.lowestY()));
		assertTrue(p.y() + G.lowestY() < bed + 1.2, "came down to it: keel at " + (p.y() + G.lowestY()));
		assertEquals(0, dive.vy, 1e-9);
	}

	@Test
	void fallsWithoutWater() {
		Dive dive = new Dive();
		ShipPose p = run(new ShipPose(0, 80, 0, 0), dive, new ShipPhysics(), 0, Double.NaN, seaBed(64), 5);
		assertEquals(64.0, p.y() + G.lowestY(), 0.5, "rests on the ground");
	}
}
