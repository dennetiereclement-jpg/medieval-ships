package fr.medievalships.core;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.Arrays;

import org.junit.jupiter.api.Test;

/**
 * The rule that keeps the world's water from being drawn across the rooms of a vessel (1.28.0, {@link
 * InteriorGrid#hidesWater}; the client's {@code DryWater} applies it to every water block near a hull): 27 samples of
 * the block, hidden when one is dry and none outside the hull, a block straddling the outer hull only when the dry
 * samples outnumber the outside ones; since 1.28.1 a block whose top face (the surface of the sea) lies wholly within the
 * hull, in a dry cell, is hidden whatever lies under it. Checked on a synthetic box hull with a floor slab and an
 * airlock, at several poses, on the same box with a shell thinner than the spacing of the samples, then on the Old
 * Corsair's real grid (its hold and its companionway lie under the waterline).
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
		assertArrayEquals(new int[] {0, 27, 0, 0, 9}, g.waterSamples(pose, 100, 51, 200, CLOSED));
		assertTrue(g.hidesWater(pose, 98, 48, 199, CLOSED));
		// a block whose centre is in the floor slab, its top face in the room above (the slab is thinner than the block)
		assertArrayEquals(new int[] {0, 27, 0, 0, 9}, g.waterSamples(pose, 100, 50, 200, CLOSED));
		assertTrue(g.hidesWater(pose, 100, 50, 200, CLOSED));
		// a block wholly in the shell: hidden (the wall is drawn over it); one wholly outside: the sea, drawn
		assertTrue(g.hidesWater(pose, 104, 51, 200, CLOSED));
		assertArrayEquals(new int[] {27, 0, 0, 9, 0}, g.waterSamples(pose, 105, 51, 200, CLOSED));
		assertFalse(g.hidesWater(pose, 105, 51, 200, CLOSED));
		assertFalse(g.hidesWater(pose, 100, 55, 200, CLOSED)); // above the hull
		assertFalse(g.hidesWater(pose, 100, 46, 200, CLOSED)); // under the keel
		assertFalse(g.hidesWater(pose, 130, 51, 200, CLOSED)); // the open sea (fast path)
		assertArrayEquals(new int[] {27, 0, 0, 9, 0}, g.waterSamples(pose, 130, 51, 200, CLOSED));
	}

	@Test
	void blocksStraddlingTheOuterHull() {
		InteriorGrid g = box();
		// the hull's side (x 4..5 ship-local) at world x 104.3..105.3: the block 104 is 0.7 in the hull, 0.3 in the room
		ShipPose pose = new ShipPose(100.3, 50, 200, 0);
		assertArrayEquals(new int[] {0, 27, 0, 0, 9}, g.waterSamples(pose, 104, 51, 200, CLOSED));
		assertTrue(g.hidesWater(pose, 104, 51, 200, CLOSED));
		// the block 105 (ship-local x 4.7..5.7): one column of samples in the shell, two outside: drawn
		assertArrayEquals(new int[] {18, 9, 0, 6, 3}, g.waterSamples(pose, 105, 51, 200, CLOSED));
		assertFalse(g.hidesWater(pose, 105, 51, 200, CLOSED));
		// moved 0.3 further: the block 105 (ship-local x 4.4..5.4) has two columns in the shell, one outside: hidden
		pose = new ShipPose(100.6, 50, 200, 0);
		assertArrayEquals(new int[] {9, 18, 0, 3, 6}, g.waterSamples(pose, 105, 51, 200, CLOSED));
		assertTrue(g.hidesWater(pose, 105, 51, 200, CLOSED));
		assertTrue(g.hidesWater(pose, 104, 51, 200, CLOSED));
		assertFalse(g.hidesWater(pose, 106, 51, 200, CLOSED));
		// the rule on the counts alone
		assertTrue(InteriorGrid.hidesWater(new int[] {0, 1, 26}));
		assertTrue(InteriorGrid.hidesWater(new int[] {13, 14, 0}));
		assertFalse(InteriorGrid.hidesWater(new int[] {14, 13, 0}));
		assertFalse(InteriorGrid.hidesWater(new int[] {0, 0, 27, 0, 0}));
		assertFalse(InteriorGrid.hidesWater(new int[] {27, 0, 0, 9, 0}));
		// with the top face counted (1.28.1): wholly dry, hidden whatever lies below; partly outside, the majority rule
		assertTrue(InteriorGrid.hidesWater(new int[] {18, 9, 0, 0, 9}));
		assertTrue(InteriorGrid.hidesWater(new int[] {26, 1, 0, 0, 1}));
		assertFalse(InteriorGrid.hidesWater(new int[] {18, 9, 0, 6, 3}));
		assertTrue(InteriorGrid.hidesWater(new int[] {9, 18, 0, 3, 6}));
		assertFalse(InteriorGrid.hidesWater(new int[] {27, 0, 0, 9, 0}));
	}

	/** The same box with 0.25 cells and a shell only 0.25 thick: a floor thinner than the spacing of the samples. */
	private static InteriorGrid thinBox() {
		int nx = 40, ny = 24, nz = 40;
		double x0 = -5, y0 = -3, z0 = -5, cell = 0.25;
		byte[] cells = new byte[nx * ny * nz];
		for (int ix = 0; ix < nx; ix++) {
			for (int iz = 0; iz < nz; iz++) {
				for (int iy = 0; iy < ny; iy++) {
					double x = x0 + (ix + 0.5) * cell, y = y0 + (iy + 0.5) * cell, z = z0 + (iz + 0.5) * cell;
					boolean shell = Math.abs(x) > 4.75 || Math.abs(z) > 4.75 || y < -2.75 || y > 2.75;
					cells[(ix * nz + iz) * ny + iy] = shell ? InteriorGrid.SOLID : InteriorGrid.DRY;
				}
			}
		}
		return new InteriorGrid(nx, ny, nz, x0, y0, z0, cell, cells);
	}

	@Test
	void aFloorThinnerThanTheSamples() {
		InteriorGrid g = thinBox();
		// the shell's bottom (local y -3..-2.75) at world 47.52..47.77: the block at y 47 has its lower samples (47.1, 47.5)
		// under the hull and its top face (47.889) in the room: the surface of the sea would show 0.12 above the floor
		ShipPose pose = new ShipPose(100, 50.52, 200, 0);
		assertArrayEquals(new int[] {18, 9, 0, 0, 9}, g.waterSamples(pose, 100, 47, 200, CLOSED));
		assertTrue(g.hidesWater(pose, 100, 47, 200, CLOSED));
		// the block above is wholly in the room, the one below wholly under the keel
		assertArrayEquals(new int[] {0, 27, 0, 0, 9}, g.waterSamples(pose, 100, 48, 200, CLOSED));
		assertTrue(g.hidesWater(pose, 100, 48, 200, CLOSED));
		assertArrayEquals(new int[] {27, 0, 0, 9, 0}, g.waterSamples(pose, 100, 46, 200, CLOSED));
		assertFalse(g.hidesWater(pose, 100, 46, 200, CLOSED));
		// the shell a little higher (world 47.82..48.07): the top face lies in the shell itself, under the floor: hidden too
		// (the hull is drawn over it)
		pose = new ShipPose(100, 50.82, 200, 0);
		assertArrayEquals(new int[] {18, 9, 0, 0, 9}, g.waterSamples(pose, 100, 47, 200, CLOSED));
		assertTrue(g.hidesWater(pose, 100, 47, 200, CLOSED));
		// higher still (48.02..48.27): the whole block is under the keel: drawn
		pose = new ShipPose(100, 51.02, 200, 0);
		assertArrayEquals(new int[] {27, 0, 0, 9, 0}, g.waterSamples(pose, 100, 47, 200, CLOSED));
		assertFalse(g.hidesWater(pose, 100, 47, 200, CLOSED));
		// every offset of the floor over the block grid: under the middle of the hull, a block is hidden exactly when its
		// top face is at or above the hull's bottom (in the shell or the room), never when it lies wholly under the keel
		for (double off = 0.03; off < 1; off += 0.05) {
			pose = new ShipPose(100, 50 + off, 200, 0);
			for (int by = 45; by <= 49; by++) {
				boolean topInside = by + 8.0 / 9.0 > 47 + off;
				assertEquals(topInside, g.hidesWater(pose, 100, by, 200, CLOSED),
						"floor at " + (47 + off) + ", block " + by + ": " + Arrays.toString(g.waterSamples(pose, 100, by, 200, CLOSED)));
			}
		}
	}

	@Test
	void theThinShellBesideTheSea() {
		InteriorGrid g = thinBox();
		// the side (local x 4.75..5) at world 104.98..105.3: the block 104 is wholly in the room, the block 105 has one column
		// of samples in the shell and two outside, its top face partly outside: the majority rule, drawn (no hole in the sea)
		ShipPose pose = new ShipPose(100.3, 50, 200, 0);
		assertArrayEquals(new int[] {0, 27, 0, 0, 9}, g.waterSamples(pose, 104, 51, 200, CLOSED));
		assertTrue(g.hidesWater(pose, 104, 51, 200, CLOSED));
		assertArrayEquals(new int[] {18, 9, 0, 6, 3}, g.waterSamples(pose, 105, 51, 200, CLOSED));
		assertFalse(g.hidesWater(pose, 105, 51, 200, CLOSED));
		assertFalse(g.hidesWater(pose, 106, 51, 200, CLOSED));
		// at every offset of the wall over the block grid: a block wholly outside is drawn, and a block whose top face has a
		// sample outside the hull is hidden only by the majority rule
		for (double off = 0.03; off < 1; off += 0.05) {
			pose = new ShipPose(100 + off, 50, 200, 0);
			for (int bx = 103; bx <= 107; bx++) {
				int[] s = g.waterSamples(pose, bx, 51, 200, CLOSED);
				boolean hides = g.hidesWater(pose, bx, 51, 200, CLOSED);
				String where = "wall at " + (105 + off) + ", block " + bx + ": " + Arrays.toString(s);
				if (s[0] == 27) {
					assertFalse(hides, where);
				}
				if (s[3] > 0) {
					assertEquals(s[1] > 0 && (s[0] == 0 || s[1] > s[0]), hides, where);
				}
			}
		}
	}

	@Test
	void thinFloorsUnderTurnedHulls() {
		InteriorGrid g = thinBox();
		for (double yaw = -180; yaw < 180; yaw += 23) {
			// the floor at world 47.52..47.77 whatever the heading: the blocks at y 47 under the middle of the hull have their
			// top face in the room and their body under the keel: hidden; the sea 20 blocks away is drawn
			ShipPose pose = new ShipPose(1000.37, 50.52, -500.81, yaw);
			for (int dx = -2; dx <= 2; dx++) {
				for (int dz = -2; dz <= 2; dz++) {
					int[] s = g.waterSamples(pose, 1000 + dx, 47, -501 + dz, CLOSED);
					assertEquals(0, s[3], "yaw " + yaw + " at " + dx + ", " + dz + ": " + Arrays.toString(s));
					assertTrue(s[0] >= 18, "yaw " + yaw + " at " + dx + ", " + dz + ": " + Arrays.toString(s));
					assertTrue(g.hidesWater(pose, 1000 + dx, 47, -501 + dz, CLOSED), "yaw " + yaw + " at " + dx + ", " + dz);
					assertFalse(g.hidesWater(pose, 1000 + dx, 46, -501 + dz, CLOSED), "yaw " + yaw + " under the keel at " + dx + ", " + dz);
					assertFalse(g.hidesWater(pose, 1000 + dx + 20, 47, -501 + dz, CLOSED), "yaw " + yaw + " at " + (dx + 20) + ", " + dz);
				}
			}
			// beside the hull (the shell ends at 5): the sea, drawn
			double[] w = pose.toWorld(5.6, 1.5, 0);
			assertFalse(g.hidesWater(pose, (int) Math.floor(w[0]), 51, (int) Math.floor(w[2]), CLOSED), "yaw " + yaw + " beside the hull");
		}
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
		assertArrayEquals(new int[] {0, 27, 0, 0, 9}, g.waterSamples(pose, 102, 48, 202, CLOSED));
		assertTrue(g.hidesWater(pose, 102, 48, 202, CLOSED));
		InteriorGrid.State flooded = CLOSED.withAirlock(1f);
		assertArrayEquals(new int[] {0, 0, 27, 0, 0}, g.waterSamples(pose, 102, 48, 202, flooded));
		assertFalse(g.hidesWater(pose, 102, 48, 202, flooded));
		// half full (water at -1.25): the block -2..-1 is wet below the water, dry above it: the vessel draws its own
		// water there, the world's is not drawn
		InteriorGrid.State half = CLOSED.withAirlock(0.5f);
		assertArrayEquals(new int[] {0, 9, 18, 0, 9}, g.waterSamples(pose, 102, 48, 202, half));
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
		// 1.30.0: the ship rides half a block deeper, the floor of the lower deck at the sea level (its rooms dry: the grid)
		assertTrue(CorsairLayout.HOLD_FLOOR_Y < h.waterlineY - 1.5 && Math.abs(CorsairLayout.LOWER_FLOOR_Y - h.waterlineY) < 1e-9);
	}
}
