package fr.medievalships.core;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import org.junit.jupiter.api.Test;

/**
 * The rule that keeps the world's water from being drawn across the rooms of a vessel (1.28.0, {@link
 * InteriorGrid#hidesWater}; the client's {@code DryWater} applies it to every water block near a hull): 27 samples of
 * the block, hidden when one is dry and none outside the hull, a block straddling the outer hull only when the dry
 * samples outnumber the outside ones. Checked on a synthetic box hull with a floor slab and an airlock, at several
 * poses, then on the Old Corsair's real grid (its hold and its companionway lie under the waterline).
 */
class DryWaterTest {
	private static final InteriorGrid.State CLOSED = InteriorGrid.State.CLOSED;

	/**
	 * A box hull 10 x 6 x 10 (x -5..5, y -3..3, z -5..5) in 0.5 cells: a solid shell one cell thick, rooms inside, a
	 * floor slab 0.5 thick at y 0..0.5, an airlock (x 2..4, z 2..4, y -2.5..0) in the lower room.
	 */
	private static InteriorGrid box() {
		int nx = 20, ny = 12, nz = 20;
		double x0 = -5, y0 = -3, z0 = -5, cell = 0.5;
		byte[] cells = new byte[nx * ny * nz];
		for (int ix = 0; ix < nx; ix++) {
			for (int iz = 0; iz < nz; iz++) {
				for (int iy = 0; iy < ny; iy++) {
					double x = x0 + (ix + 0.5) * cell, y = y0 + (iy + 0.5) * cell, z = z0 + (iz + 0.5) * cell;
					byte k;
					if (Math.abs(x) > 4 || Math.abs(z) > 4 || y < -2.5 || y > 2.5) {
						k = InteriorGrid.SOLID; // the shell
					} else if (y > 0 && y < 0.5) {
						k = InteriorGrid.SOLID; // the floor slab
					} else if (x > 2 && z > 2 && y < 0) {
						k = InteriorGrid.AIRLOCK;
					} else {
						k = InteriorGrid.DRY;
					}
					cells[(ix * nz + iz) * ny + iy] = k;
				}
			}
		}
		return new InteriorGrid(nx, ny, nz, x0, y0, z0, cell, cells);
	}

	@Test
	void roomsFloorsAndTheOpenSea() {
		InteriorGrid g = box();
		ShipPose pose = new ShipPose(100, 50, 200, 0); // ship-local = world - (100, 50, 200)
		assertEquals(-2.5, g.airlockFloor, 1e-9);
		assertEquals(0.0, g.airlockTop, 1e-9);
		// in the upper room: hidden; in the lower room too
		assertTrue(g.hidesWater(pose, 100, 51, 200, CLOSED));
		assertArrayEquals(new int[] {0, 27, 0}, g.waterSamples(pose, 100, 51, 200, CLOSED));
		assertTrue(g.hidesWater(pose, 98, 48, 199, CLOSED));
		// a block whose centre is in the floor slab, its top face in the room above (the slab is thinner than the block)
		assertArrayEquals(new int[] {0, 27, 0}, g.waterSamples(pose, 100, 50, 200, CLOSED));
		assertTrue(g.hidesWater(pose, 100, 50, 200, CLOSED));
		// a block wholly in the shell: hidden (the wall is drawn over it); one wholly outside: the sea, drawn
		assertTrue(g.hidesWater(pose, 104, 51, 200, CLOSED));
		assertArrayEquals(new int[] {27, 0, 0}, g.waterSamples(pose, 105, 51, 200, CLOSED));
		assertFalse(g.hidesWater(pose, 105, 51, 200, CLOSED));
		assertFalse(g.hidesWater(pose, 100, 55, 200, CLOSED)); // above the hull
		assertFalse(g.hidesWater(pose, 100, 46, 200, CLOSED)); // under the keel
		assertFalse(g.hidesWater(pose, 130, 51, 200, CLOSED)); // the open sea (fast path)
		assertArrayEquals(new int[] {27, 0, 0}, g.waterSamples(pose, 130, 51, 200, CLOSED));
	}

	@Test
	void blocksStraddlingTheOuterHull() {
		InteriorGrid g = box();
		// the hull's side (x 4..5 ship-local) at world x 104.3..105.3: the block 104 is 0.7 in the hull, 0.3 in the room
		ShipPose pose = new ShipPose(100.3, 50, 200, 0);
		assertArrayEquals(new int[] {0, 27, 0}, g.waterSamples(pose, 104, 51, 200, CLOSED));
		assertTrue(g.hidesWater(pose, 104, 51, 200, CLOSED));
		// the block 105 (ship-local x 4.7..5.7): one column of samples in the shell, two outside: drawn
		assertArrayEquals(new int[] {18, 9, 0}, g.waterSamples(pose, 105, 51, 200, CLOSED));
		assertFalse(g.hidesWater(pose, 105, 51, 200, CLOSED));
		// moved 0.3 further: the block 105 (ship-local x 4.4..5.4) has two columns in the shell, one outside: hidden
		pose = new ShipPose(100.6, 50, 200, 0);
		assertArrayEquals(new int[] {9, 18, 0}, g.waterSamples(pose, 105, 51, 200, CLOSED));
		assertTrue(g.hidesWater(pose, 105, 51, 200, CLOSED));
		assertTrue(g.hidesWater(pose, 104, 51, 200, CLOSED));
		assertFalse(g.hidesWater(pose, 106, 51, 200, CLOSED));
		// the rule on the counts alone
		assertTrue(InteriorGrid.hidesWater(new int[] {0, 1, 26}));
		assertTrue(InteriorGrid.hidesWater(new int[] {13, 14, 0}));
		assertFalse(InteriorGrid.hidesWater(new int[] {14, 13, 0}));
		assertFalse(InteriorGrid.hidesWater(new int[] {0, 0, 27}));
		assertFalse(InteriorGrid.hidesWater(new int[] {27, 0, 0}));
	}

	@Test
	void turnedHulls() {
		InteriorGrid g = box();
		// facing west: ship-local x = world dz, ship-local z = -world dx
		ShipPose west = new ShipPose(100, 50, 200, 90);
		assertTrue(g.hidesWater(west, 100, 51, 200, CLOSED));
		assertTrue(g.hidesWater(west, 97, 51, 203, CLOSED));
		assertFalse(g.hidesWater(west, 100, 51, 210, CLOSED));
		assertFalse(g.hidesWater(west, 110, 51, 200, CLOSED));
		// any heading: the blocks around the origin are in the rooms, those 20 blocks away in the sea
		for (double yaw = -180; yaw < 180; yaw += 23) {
			ShipPose pose = new ShipPose(1000.37, 50.2, -500.81, yaw);
			for (int dx = -2; dx <= 2; dx++) {
				for (int dz = -2; dz <= 2; dz++) {
					assertTrue(g.hidesWater(pose, 1000 + dx, 51, -501 + dz, CLOSED), "yaw " + yaw + " at " + dx + ", " + dz);
					assertFalse(g.hidesWater(pose, 1000 + dx + 20, 51, -501 + dz, CLOSED), "yaw " + yaw + " at " + (dx + 20) + ", " + dz);
					assertFalse(g.hidesWater(pose, 1000 + dx, 51, -501 + dz - 20, CLOSED), "yaw " + yaw + " at " + dx + ", " + (dz - 20));
				}
			}
			// the shell is 0.5 thick: a block 5 to 6 out along the hull's x axis is wholly outside whatever the heading
			double[] w = pose.toWorld(5.5, 1.5, 0);
			assertFalse(g.hidesWater(pose, (int) Math.floor(w[0]), 51, (int) Math.floor(w[2]), CLOSED), "yaw " + yaw + " beside the hull");
		}
	}

	@Test
	void airlock() {
		InteriorGrid g = box();
		ShipPose pose = new ShipPose(100, 50, 200, 0);
		// the airlock (ship-local x 2..4, y -2.5..0, z 2..4): pumped out it is dry, flooded it is the sea
		assertArrayEquals(new int[] {0, 27, 0}, g.waterSamples(pose, 102, 48, 202, CLOSED));
		assertTrue(g.hidesWater(pose, 102, 48, 202, CLOSED));
		InteriorGrid.State flooded = CLOSED.withAirlock(1f);
		assertArrayEquals(new int[] {0, 0, 27}, g.waterSamples(pose, 102, 48, 202, flooded));
		assertFalse(g.hidesWater(pose, 102, 48, 202, flooded));
		// half full (water at -1.25): the block -2..-1 is wet below the water, dry above it: the vessel draws its own
		// water there, the world's is not drawn
		InteriorGrid.State half = CLOSED.withAirlock(0.5f);
		assertArrayEquals(new int[] {0, 9, 18}, g.waterSamples(pose, 102, 48, 202, half));
		assertTrue(g.hidesWater(pose, 102, 48, 202, half));
		// the room beside the airlock stays dry whatever its level
		assertTrue(g.hidesWater(pose, 98, 48, 198, flooded));
	}

	@Test
	void theOldCorsairsHoldAndCompanionway() {
		ShipGeometry g = Ships.OLD_CORSAIR.geometry();
		InteriorGrid grid = g.interior();
		HullShape h = g.hull();
		// afloat on a sea whose surface is at world y 63.89 (the top of the water blocks at y 63), heading north-west
		ShipPose pose = new ShipPose(10.25, 63.89 - h.waterlineY, -40.6, 135);
		int hidden = 0, drawn = 0, straddling = 0;
		for (int bx = -20; bx <= 40; bx++) {
			for (int bz = -70; bz <= -10; bz++) {
				for (int by = 56; by <= 63; by++) {
					int[] s = grid.waterSamples(pose, bx, by, bz, CLOSED);
					boolean hides = grid.hidesWater(pose, bx, by, bz, CLOSED);
					assertEquals(InteriorGrid.hidesWater(s), hides);
					if (s[0] == 27) {
						assertFalse(hides, "the open sea at " + bx + " " + by + " " + bz);
						drawn++;
					} else if (s[0] == 0) {
						assertTrue(hides, "inside the hull at " + bx + " " + by + " " + bz);
						hidden++;
					} else {
						straddling++;
					}
				}
			}
		}
		assertTrue(hidden > 500 && drawn > 20000 && straddling > 200, hidden + " hidden, " + drawn + " drawn, " + straddling + " straddling");
		// the surface of the sea (the blocks at y 63, their top face at the sea level) over the hold (floor -2) and over the
		// companionway down to it (x -1..1, z -17..-14), which lie under the sea: hidden all along the centre line
		int over = 0;
		for (double lz = -16.5; lz <= 12.5; lz += 0.5) {
			double[] w = pose.toWorld(0, 0, lz);
			int bx = (int) Math.floor(w[0]), bz = (int) Math.floor(w[2]);
			int[] s = grid.waterSamples(pose, bx, 63, bz, CLOSED);
			assertEquals(0, s[0], "over the hold at z " + lz + ": samples outside the hull");
			assertTrue(s[1] > 0 && grid.hidesWater(pose, bx, 63, bz, CLOSED), "over the hold at z " + lz);
			over++;
		}
		assertTrue(over >= 59, "blocks over the hold: " + over);
		assertTrue(CorsairLayout.HOLD_FLOOR_Y < h.waterlineY - 1.5 && CorsairLayout.LOWER_FLOOR_Y > h.waterlineY + 0.3);
	}
}
