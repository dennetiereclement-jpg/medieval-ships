package fr.medievalships.core;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.List;

import org.junit.jupiter.api.Test;

import fr.medievalships.core.Ships.MedievalGalleyLayout;
import fr.medievalships.core.Ships.PaddleboatLayout;

/**
 * Gameplay geometry and handling of the ships added after the warship (red medieval galley...):
 * the same checks for every one of them, plus the values shared with their model generators.
 */
class NewShipsTest {
	private static final List<ShipType> NEW = List.of(Ships.MEDIEVAL_GALLEY, Ships.STEAM_PADDLEBOAT, Ships.ELVEN_SAILBOAT);
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

	/** Values printed by {@code python3 tools/paddleboat_shape.py}: z, half width, rail, keel, bottom at 2. */
	@Test
	void paddleboatMatchesModelGenerator() {
		HullShape h = Ships.STEAM_PADDLEBOAT.hull();
		double[][] expected = {
				{-10.0, 2.658552, 3.481406, -1.224108, -0.951815},
				{-6.0, 3.788572, 3.365306, -1.725364, -1.634282},
				{0.0, 4.000000, 3.300000, -1.800000, -1.710000},
				{5.0, 3.423651, 3.379365, -1.764007, -1.660958},
				{10.0, 1.309232, 3.617460, -1.224108, -0.220339}};
		for (double[] e : expected) {
			assertEquals(e[1], h.halfWidth(e[0]), 1e-5);
			assertEquals(e[2], h.railY(e[0]), 1e-5);
			assertEquals(e[3], h.keelY(e[0]), 1e-5);
			assertEquals(e[4], h.bottomY(e[0], 2.0), 1e-5);
		}
	}

	@Test
	void paddleboatDimensions() {
		HullShape h = Ships.STEAM_PADDLEBOAT.hull();
		ShipGeometry g = Ships.STEAM_PADDLEBOAT.geometry();
		assertEquals(22.4, 2 * h.tip, 1e-9);
		assertEquals(8.0, 2 * h.maxHalfWidth, 1e-9);
		double hull = h.railY(0) - h.keelY(0);
		assertTrue(hull > 4.8 && hull < 5.4, "hull height " + hull);
		double total = PaddleboatLayout.FUNNEL_TOP - h.keelY(0);
		assertTrue(total > 12 && total < 13, "total height " + total);
		assertEquals(8, g.seats().size());
	}

	/** One wheel, on the starboard side: round, outside the hull, partly under water, inside its box. */
	@Test
	void paddleWheel() {
		HullShape h = Ships.STEAM_PADDLEBOAT.hull();
		ShipGeometry g = Ships.STEAM_PADDLEBOAT.geometry();
		double z = PaddleboatLayout.WHEEL_Z, r = PaddleboatLayout.WHEEL_R;
		// clear of the hull side over its whole height
		for (double y = PaddleboatLayout.WHEEL_Y - r; y <= PaddleboatLayout.WHEEL_Y + r; y += 0.25) {
			assertTrue(PaddleboatLayout.WHEEL_X0 > h.halfWidth(z) + 0.1, "the wheel cuts into the hull");
		}
		// partly immersed: about a third of its diameter under water, the axle above it
		double under = h.waterlineY - (PaddleboatLayout.WHEEL_Y - r);
		assertTrue(under > 0.6 && under < 1.6, "immersion " + under);
		assertTrue(PaddleboatLayout.WHEEL_Y > h.waterlineY + 1);
		assertTrue(PaddleboatLayout.BOX_X1 > PaddleboatLayout.WHEEL_X1);
		// the box above it is solid (players, swimmers), and the autopilot knows how wide the ship is
		assertTrue(intersectsSolid(g, -(PaddleboatLayout.WHEEL_X0 + PaddleboatLayout.WHEEL_X1) / 2, PaddleboatLayout.WHEEL_Y + r - 0.2, z,
				0.2, 0.2, 0.2));
		assertTrue(g.aiHalfWidth() > PaddleboatLayout.WHEEL_X1 - 0.5);
		assertFalse(intersectsSolid(g, (PaddleboatLayout.WHEEL_X0 + PaddleboatLayout.WHEEL_X1) / 2, PaddleboatLayout.WHEEL_Y + r - 0.2, z,
				0.2, 0.2, 0.2), "only one wheel, on the starboard side");
	}

	@Test
	void paddleboatHandlesLikeASteamer() {
		ShipConfig steam = Ships.STEAM_PADDLEBOAT.defaults().get(), galley = Ships.MEDIEVAL_GALLEY.defaults().get();
		// progressive acceleration, good low speed handling, no sail to furl
		assertTrue(steam.acceleration < galley.acceleration);
		assertTrue(steam.minTurnFactor > galley.minTurnFactor);
		assertFalse(steam.furlSailWhenStopped);
	}

	/** Values printed by {@code python3 tools/elven_shape.py}: z, half width, rail, keel, bottom at 1.5. */
	@Test
	void elvenMatchesModelGenerator() {
		HullShape h = Ships.ELVEN_SAILBOAT.hull();
		double[][] expected = {
				{-11.0, 1.241462, 2.815406, -0.854144, -0.102497},
				{-6.0, 2.591192, 2.062132, -1.670190, -1.227988},
				{0.0, 3.000000, 1.850000, -1.900000, -1.535000},
				{6.0, 2.319442, 2.132843, -1.670190, -1.123653},
				{11.0, 0.891545, 3.137208, -0.854144, -0.102497}};
		for (double[] e : expected) {
			assertEquals(e[1], h.halfWidth(e[0]), 1e-5);
			assertEquals(e[2], h.railY(e[0]), 1e-5);
			assertEquals(e[3], h.keelY(e[0]), 1e-5);
			assertEquals(e[4], h.bottomY(e[0], 1.5), 1e-5);
		}
	}

	@Test
	void elvenDimensions() {
		HullShape h = Ships.ELVEN_SAILBOAT.hull();
		assertEquals(6.0, 2 * h.maxHalfWidth, 1e-9);
		// 24 block hull, 30 overall with the carved stern and the long prow
		double overall = Ships.ElvenLayout.PROW_TIP_Z + 14.3;
		assertTrue(overall > 29.5 && overall < 31.5, "overall " + overall);
		double hull = h.railY(0) - h.keelY(0);
		assertTrue(hull > 3.5 && hull < 4.2, "hull height " + hull);
		double total = Ships.ElvenLayout.MAST_TOP - h.keelY(0);
		assertTrue(total > 19.5 && total < 22, "total height " + total);
		assertEquals(8, Ships.ELVEN_SAILBOAT.geometry().seats().size());
	}

	@Test
	void elvenIsFastAndFluid() {
		ShipConfig elf = Ships.ELVEN_SAILBOAT.defaults().get(), galleon = Ships.GALLEON.defaults().get();
		ShipConfig red = Ships.MEDIEVAL_GALLEY.defaults().get();
		assertTrue(elf.fastSpeed > red.fastSpeed && elf.fastSpeed > galleon.fastSpeed);
		// lighter than the big human ships, and a long glide
		assertTrue(elf.acceleration > galleon.acceleration && elf.waterDrag < red.waterDrag);
	}

	@Test
	void identifiersAndAliases() {
		assertEquals(Ships.MEDIEVAL_GALLEY, Ships.byId("medieval_galley"));
		assertEquals(Ships.STEAM_PADDLEBOAT, Ships.byId("steam_paddleboat"));
		assertEquals(Ships.ELVEN_SAILBOAT, Ships.byId("elven_sailboat"));
		// the great warship keeps its id (saves, configs) and is also known as grand_warship
		assertEquals(Ships.WARSHIP, Ships.byId("grand_warship"));
		assertEquals("warship", Ships.WARSHIP.id());
		assertEquals(6, Ships.ALL.size());
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
