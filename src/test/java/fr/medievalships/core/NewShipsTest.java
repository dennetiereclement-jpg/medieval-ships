package fr.medievalships.core;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.List;

import org.junit.jupiter.api.Test;

import fr.medievalships.core.Ships.MedievalGalleyLayout;

/**
 * Gameplay geometry and handling of the ships added after the warship (red medieval galley...):
 * the same checks for every one of them, plus the values shared with their model generators.
 */
class NewShipsTest {
	private static final List<ShipType> NEW = List.of(Ships.MEDIEVAL_GALLEY);
	private static final ShipPose ORIGIN = new ShipPose(0, 0, 0, 0);

	private static boolean intersectsSolid(ShipGeometry g, double x, double y, double z, double hx, double h, double hz) {
		boolean[] hit = {false};
		g.collectBoxes(ORIGIN, x - hx, y, z - hz, x + hx, y + h, z + hz, (a, b, c, d, e, f) -> {
			if (a < x + hx - 1e-6 && d > x - hx + 1e-6 && b < y + h - 1e-6 && e > y + 1e-6 && c < z + hz - 1e-6 && f > z - hz + 1e-6) {
				hit[0] = true;
			}
		});
		return hit[0];
	}

	private static double support(ShipGeometry g, double x, double y, double z) {
		double[] top = {Double.NEGATIVE_INFINITY};
		g.collectBoxes(ORIGIN, x - 0.3, y - 8, z - 0.3, x + 0.3, y + 0.1, z + 0.3, (a, b, c, d, e, f) -> {
			if (x + 0.3 > a && x - 0.3 < d && z + 0.3 > c && z - 0.3 < f && e <= y + 1e-3) {
				top[0] = Math.max(top[0], e);
			}
		});
		return top[0];
	}

	private static void assertStandable(ShipGeometry g, double[] feet, String what) {
		assertTrue(support(g, feet[0], feet[1], feet[2]) > feet[1] - 0.1, what + ": nothing to stand on at " + str(feet));
		assertFalse(intersectsSolid(g, feet[0], feet[1] + 0.03, feet[2], 0.3, 1.8, 0.3), what + ": inside a wall at " + str(feet));
	}

	private static String str(double[] p) {
		return String.format(java.util.Locale.ROOT, "(%.2f, %.2f, %.2f)", p[0], p[1], p[2]);
	}

	// ------------------------------------------------------------------ shared with the generators

	/** Values printed by {@code python3 tools/medieval_galley_shape.py}: z, half width, rail, keel, bottom at 1.2. */
	@Test
	void medievalGalleyMatchesModelGenerator() {
		HullShape h = Ships.MEDIEVAL_GALLEY.hull();
		double[][] expected = {
				{-12.0, 0.694873, 3.650443, -0.213395, -0.021339},
				{-8.0, 1.811095, 2.313094, -0.942858, -0.663283},
				{0.0, 2.500000, 1.750000, -1.250000, -1.106000},
				{6.0, 2.132666, 1.987555, -1.120424, -0.909730},
				{12.0, 0.694873, 3.650443, -0.213395, -0.021339}};
		for (double[] e : expected) {
			assertEquals(e[1], h.halfWidth(e[0]), 1e-5);
			assertEquals(e[2], h.railY(e[0]), 1e-5);
			assertEquals(e[3], h.keelY(e[0]), 1e-5);
			assertEquals(e[4], h.bottomY(e[0], 1.2), 1e-5);
		}
	}

	@Test
	void medievalGalleyDimensions() {
		HullShape h = Ships.MEDIEVAL_GALLEY.hull();
		ShipGeometry g = Ships.MEDIEVAL_GALLEY.geometry();
		assertEquals(27.2, 2 * h.tip, 1e-9);          // 28 with the dragon heads
		assertEquals(5.0, 2 * h.maxHalfWidth, 1e-9);
		double hull = h.railY(0) - h.keelY(0);
		assertTrue(hull > 2.8 && hull < 3.2, "hull height " + hull);
		// crescent: the ends rise more than 1.5 blocks above the waist
		assertTrue(h.railY(12) - h.railY(0) > 1.5);
		assertTrue(MedievalGalleyLayout.MAST_TOP - h.waterlineY > 13 && MedievalGalleyLayout.MAST_TOP - h.waterlineY < 15);
		assertEquals(10, g.seats().size());
	}

	// ------------------------------------------------------------------ every new ship

	@Test
	void seatsAndDismountsAreFree() {
		for (ShipType t : NEW) {
			ShipGeometry g = t.geometry();
			List<ShipGeometry.Seat> seats = g.seats();
			for (int i = 0; i < seats.size(); i++) {
				ShipGeometry.Seat s = seats.get(i);
				assertEquals(i, s.index());
				assertEquals(i == ShipGeometry.PILOT_SEAT, s.pilot());
				assertStandable(g, s.dismountLocal(), t.id() + " dismount of seat " + i);
				assertFalse(intersectsSolid(g, s.x(), s.y() + 0.05, s.z(), 0.25, 1.2, 0.25), t.id() + " seat " + i + " inside a solid");
			}
		}
	}

	@Test
	void deckIsWalkableAtAnyHeading() {
		for (ShipType t : NEW) {
			ShipGeometry g = t.geometry();
			HullShape h = g.hull();
			for (double yaw = 0; yaw < 360; yaw += 30) {
				ShipPose pose = new ShipPose(100.3, 62.9, -40.7, yaw);
				for (double z = h.deckMinZ + 0.5; z <= h.deckMaxZ - 0.5; z += 0.43) {
					double w = h.innerHalfWidth(z) - 0.3;
					for (double x = -w; x <= w; x += 0.37) {
						double[] p = pose.toWorld(x, h.deckY(z), z);
						double[] best = {Double.NEGATIVE_INFINITY};
						g.collectBoxes(pose, p[0] - 0.3, p[1] - 0.5, p[2] - 0.3, p[0] + 0.3, p[1] + 1.8, p[2] + 0.3,
								(a, b, c, d, e, f) -> {
									if (p[0] > a && p[0] < d && p[2] > c && p[2] < f && e <= p[1] + 1e-6) {
										best[0] = Math.max(best[0], e);
									}
								});
						assertTrue(best[0] > p[1] - 0.05, t.id() + ": no deck under " + x + "," + z + " yaw " + yaw);
					}
				}
			}
		}
	}

	@Test
	void boardingSpots() {
		for (ShipType t : NEW) {
			ShipGeometry g = t.geometry();
			HullShape h = g.hull();
			for (double z = -h.halfLength; z <= h.halfLength; z += 0.25) {
				for (double x = -h.maxHalfWidth - 1; x <= h.maxHalfWidth + 1; x += 0.5) {
					assertStandable(g, g.boardingSpot(x, z), t.id() + " boarding spot for " + x + "," + z);
				}
			}
		}
	}

	@Test
	void pickingTheHelmAndTheHull() {
		for (ShipType t : NEW) {
			ShipGeometry g = t.geometry();
			ShipGeometry.LocalBox helm = g.helm();
			double hx = (helm.minX() + helm.maxX()) / 2, hy = (helm.minY() + helm.maxY()) / 2, hz = (helm.minZ() + helm.maxZ()) / 2;
			ShipGeometry.Pick p = g.pick(ORIGIN, hx, hy + 0.3, hz + 2.5, 0, -0.1, -1, 6);
			assertNotNull(p, t.id() + " helm");
			assertEquals(ShipGeometry.PickKind.HELM, p.kind(), t.id() + " helm");
			double w = g.hull().maxHalfWidth;
			p = g.pick(ORIGIN, w + 4, g.hull().mainDeckY + 0.6, 1.0, -1, 0, 0, 8);
			assertNotNull(p, t.id() + " hull");
			assertEquals(ShipGeometry.PickKind.HULL, p.kind(), t.id() + " hull");
		}
	}

	@Test
	void floatsOnItsWaterline() {
		for (ShipType t : NEW) {
			HullShape h = t.hull();
			assertTrue(h.keelY(0) < h.waterlineY - 0.6, t.id() + ": keel under water");
			assertTrue(h.mainDeckY > h.waterlineY + 0.5, t.id() + ": deck above water");
		}
	}

	// ------------------------------------------------------------------ handling

	@Test
	void medievalGalleyIsNimble() {
		ShipConfig red = Ships.MEDIEVAL_GALLEY.defaults().get(), galleon = Ships.GALLEON.defaults().get();
		ShipConfig galley = Ships.GALLEY.defaults().get();
		assertTrue(red.acceleration > galleon.acceleration && red.maxTurnRate > galleon.maxTurnRate);
		assertTrue(red.normalSpeed >= galley.normalSpeed);
		// the oars pivot the hull at rest
		assertTrue(red.minTurnFactor >= 0.3);
	}
}
